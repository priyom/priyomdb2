import binascii
import functools
import hashlib
import hmac
import itertools
import operator
import random
import struct
import unicodedata

import sqlalchemy
import sqlalchemy.orm

from . import saslprep
from .base import Base, TopLevel

from sqlalchemy import Column, DateTime, Unicode, Binary, Table, Integer, \
    ForeignKey, UniqueConstraint, BINARY
from sqlalchemy.orm import relationship, backref, Session

from datetime import timedelta, datetime

_secure_random = random.SystemRandom()

DEFAULT_ITERATION_COUNT = 2**14

def pbkdf2(hashfun, input_data, salt, iterations, dklen):
    """
    Derivate a key from a password. *input_data* is taken as the bytes object
    resembling the password (or other input). *hashfun* must be a callable
    returning a :mod:`hashlib`-compatible hash function. *salt* is the salt to
    be used in the PBKDF2 run, *iterations* the count of iterations. *dklen* is
    the length in bytes of the key to be derived.

    Return the derived key as :class:`bytes` object.
    """

    if dklen is not None and dklen <= 0:
        raise ValueError("Invalid length for derived key: {}".format(dklen))

    hlen = hashfun().digest_size
    if dklen is None:
        dklen = hlen

    block_count = (dklen+(hlen-1)) // hlen

    mac_base = hmac.new(input_data, None, hashfun)

    def do_hmac(data):
        mac = mac_base.copy()
        mac.update(data)
        return mac.digest()

    def calc_block(i):
        u_prev = do_hmac(salt + i.to_bytes(4, "big"))
        u_accum = u_prev
        for k in range(1, iterations):
            u_curr = do_hmac(u_prev)
            u_accum = bytes(itertools.starmap(
                operator.xor,
                zip(u_accum, u_curr)))
            u_prev = u_curr

        return u_accum

    result = b"".join(
        calc_block(i)
        for i in range(1, block_count+1))

    return result[:dklen]

def prepare_username(username):
    return saslprep.saslprep(username)

def prepare_password(password):
    return saslprep.saslprep(password).encode("utf-8")

def create_password_verifier(plaintext, iterations, salt, hashfun, length=None):
    if isinstance(plaintext, str):
        plaintext = prepare_password(plaintext)
    hashfun_constructor = functools.partial(hashlib.new, hashfun)
    hashed = pbkdf2(hashfun_constructor,
                    plaintext,
                    salt,
                    iterations,
                    length)

    return b"$".join([
        hashfun.encode("ascii"),
        str(iterations).encode("ascii"),
        binascii.b2a_base64(salt).strip(),
        binascii.b2a_base64(hashed).strip()])

def create_default_password_verifier(plaintext, salt):
    return create_password_verifier(
        plaintext, DEFAULT_ITERATION_COUNT, salt, "sha256")

def verify_password(verifier, password):
    hashfun, iterations, salt, hashed = verifier.split(b"$")
    hashfun = hashfun.decode("ascii")
    try:
        hashlib.new(hashfun)
    except ValueError as err:
        raise LookupError(
            "Hash function not supported: {}".format(hashfun)) from err
    try:
        iterations = int(iterations.decode("ascii"))
    except ValueError as err:
        raise ValueError("Hash database entry corrupted") from err

    hashfun_constructor = functools.partial(hashlib.new, hashfun)

    if isinstance(password, str):
        password = prepare_password(password)

    hashed = binascii.a2b_base64(hashed)
    salt = binascii.a2b_base64(salt)
    new_hashed = pbkdf2(hashfun_constructor,
                        password,
                        salt,
                        iterations,
                        len(hashed))

    return hmac.compare_digest(hashed, new_hashed)

class Capability(Base):
    __tablename__ = "capabilities"

    id = Column(Integer, nullable=False, primary_key=True)
    key = Column(Unicode(length=127), nullable=False)

group_capabilities = Table(
    "group_capabilities",
    Base.metadata,
    Column("capability_id", Integer, ForeignKey("capabilities.id")),
    Column("group_id", Integer, ForeignKey("groups.id"))
)

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, nullable=False, primary_key=True)
    name = Column(Unicode(length=127), nullable=False)
    supergroup_id = Column(Integer,
                           ForeignKey(__tablename__ + ".id",
                                      name="groups_fk_supergroup_id",
                                      ondelete="SET NULL"),
                           nullable=True)

    capabilities = relationship(
        Capability,
        secondary=group_capabilities,
        backref=backref("groups"))

    subgroups = relationship(
        "Group",
        backref=backref("supergroup",
                        remote_side=[id]),
        passive_deletes=False)

    ANONYMOUS = "anonymous"
    REGISTERED = "registered"
    MODERATORS = "moderators"
    ADMINS = "admins"
    WHEEL = "wheel"
    UNMODERATED = "unmoderated"

    def add_capability(self, capability):
        self.capabilities.append(capability)

    def add_user(self, user):
        self.users.append(user)

    def is_supergroup_of(self, other_group):
        subgroups = frozenset(self.subgroups)
        if other_group in subgroups:
            return True
        return any(group.is_supergroup_of(other_group)
                   for group in subgroups)

    def is_subgroup_of(self, other_group):
        if self.supergroup is None:
            return False
        if self.supergroup == other_group:
            return True
        return self.supergroup.is_subgroup_of(other_group)

    def __str__(self):
        return self.name

user_groups = Table(
    "user_groups",
    Base.metadata,
    Column("group_id", Integer, ForeignKey("groups.id")),
    Column("user_id", Integer, ForeignKey("users.id"))
)

class User(TopLevel):
    __tablename__ = "users"

    __table_args__ = (
        UniqueConstraint("loginname"),
        Base.__table_args__
    )

    id = Column(Integer, primary_key=True)

    loginname = Column(Unicode(length=63), nullable=False)
    loginname_displayed = Column(Unicode(length=63), nullable=False)
    email = Column(Unicode(length=255), nullable=False)
    password_verifier = Column(Binary(length=1023), nullable=False)
    timezone = Column(Unicode(length=127),
                      nullable=False,
                      server_default="Etc/UTC")
    locale = Column(Unicode(length=31),
                    nullable=False,
                    server_default="en_GB")

    groups = relationship(
        Group,
        secondary=user_groups,
        backref=backref("users"))

    def __init__(self, loginname, email):
        super().__init__()
        self.loginname = saslprep.saslprep(loginname)
        self.loginname_displayed = unicodedata.normalize("NFC", loginname)
        self.email = email

    def get_capabilities(self):
        return get_capabilities_from_groups(self.groups)

    def has_capability(self, key):
        session = Session.object_session(self)
        if not session:
            # fall back to inefficient method, which also works with
            # non-persisted objects
            return key in self.get_capabilities()

        return session.query(Capability.key).join(
                group_capabilities
            ).join(
                Group
            ).join(
                user_groups
            ).filter(
                user_groups.columns["user_id"] == self.id,
                Capability.key == key
            ).count() > 0

    def has_group(self, name):
        session = Session.object_session(self)
        if not session:
            # fall back to inefficient method, which also works with
            # non-persisted objects
            return get_has_group_from_groups(self.groups, name)

        return session.query(Group.name).join(
            user_groups
        ).filter(
            user_groups.columns["user_id"] == self.id,
            Group.name == name
        ).count() > 0

    def group_memberships(self):
        session = Session.object_session(self)
        if not session:
            return set(group.name for group in self.groups)

        return set(item
                   for item,
                   in session.query(
                       Group.name
                   ).filter(
                       user_groups.c.group_id == Group.id,
                       user_groups.c.user_id == self.id
                   ))

    def get_capabilities(self):
        session = Session.object_session(self)
        if not session:
            raise ValueError("Cannot get list of capabilities for non-persisted "
                             "user")

        return [cap for cap, in session.query(
            Capability.key
        ).join(
            group_capabilities
        ).join(
            Group
        ).join(
            user_groups,
        ).filter(
            user_groups.c.user_id == self.id
        ).order_by(
            Capability.key.asc()
        ).distinct()]

    def set_password_from_plaintext(self,
                                    plaintext,
                                    saltbytes=18):
        salt = _secure_random.getrandbits(saltbytes*8).to_bytes(
            saltbytes, "big")
        self.password_verifier = create_default_password_verifier(
            plaintext, salt)

    def get_stats(self):
        from . import event

        session = Session.object_session(self)
        if not session:
            raise ValueError("Cannot retrieve stats for non-persisted user")
        stats = {}
        stats["events"] = session.query(event.Event).filter(
            event.Event.submitter == self).count()
        return stats

    def __str__(self):
        return self.loginname_displayed

class UserSession(Base):
    __tablename__ = "user_sessions"

    __table_args__ = (
        UniqueConstraint("session_key"),
        Base.__table_args__
    )

    id = Column(Integer, primary_key=True)
    session_key = Column(BINARY(length=127), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    user = relationship(User,
                        backref=backref("sessions"))
    expiration = Column(DateTime, nullable=False)

    def __init__(self, from_user, lifetime=timedelta(days=7)):
        super().__init__()
        self.session_key = _secure_random.getrandbits(8*32).to_bytes(32, "big")
        self.expiration = datetime.utcnow() + lifetime
        self.user = from_user


def get_capabilities_from_groups(groups):
    return frozenset(
        capability.key
        for group in groups
        for capability in group.capabilities)

def get_has_group_from_groups(groups, group_name):
    return any(
        group.name == group_name
        for group in groups)
