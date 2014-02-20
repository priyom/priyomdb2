import binascii
import functools
import hashlib
import hmac
import itertools
import operator
import random
import struct
import unicodedata

from .base import Base

from sqlalchemy import Column, DateTime, Unicode, Binary, Table, Integer, \
    ForeignKey, UniqueConstraint, BINARY
from sqlalchemy.orm import relationship, backref

from datetime import timedelta, datetime

_secure_random = random.SystemRandom()

DEFAULT_ITERATION_COUNT = 2**14

user_capability_table = Table(
    "user_capabilities",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("capability_id", Integer, ForeignKey("capabilities.id")))

session_capability_table = Table(
    "session_capabilities",
    Base.metadata,
    Column("session_id", Integer, ForeignKey("user_sessions.id")),
    Column("capability_id", Integer, ForeignKey("capabilities.id")))

def pbkdf2(hashfun, input_data, salt, iterations, dklen):
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

def prepare_password(password):
    return unicodedata.normalize("NFC", password).encode("utf-8")

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
        binascii.b2a_base64(salt),
        binascii.b2a_base64(hashed)])


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

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    loginname = Column(Unicode(length=63), nullable=False)
    email = Column(Unicode(length=255), nullable=False)
    password_verifier = Column(Binary(length=1023), nullable=False)

    capabilities = relationship(
        "Capability",
        secondary=user_capability_table,
        backref="users")

    def __init__(self, loginname, email):
        super().__init__()
        self.loginname = loginname
        self.email = email

    def set_password_from_plaintext(self,
                                    plaintext,
                                    iterations,
                                    saltbytes=32):
        salt = _secure_random.getrandbits(saltbytes*8).to_bytes(
            saltbytes, "big")
        self.password_verifier = create_password_verifier(
            plaintext, iterations, salt, "sha256")

class UserSession(Base):
    __tablename__ = "user_sessions"

    __table_args__ = (
        UniqueConstraint("session_key"),
    )

    id = Column(Integer, primary_key=True)
    session_key = Column(BINARY(length=127), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    user = relationship(User,
                        backref=backref("sessions"))
    expiration = Column(DateTime, nullable=False)

    capabilities = relationship(
        "Capability",
        secondary=session_capability_table,
        backref="sessions")

    def __init__(self, from_user, lifetime=timedelta(days=7)):
        super().__init__()
        self.session_key = _secure_random.getrandbits(8*32).to_bytes(32, "big")
        self.expiration = datetime.utcnow() + lifetime
        self.user = from_user
        for capability in self.user.capabilities:
            self.capabilities.add(capability)

class Capability(Base):
    __tablename__ = "capabilities"

    id = Column(Integer, nullable=False, primary_key=True)
    key = Column(Unicode(length=127), nullable=False)
    display_name = Column(Unicode(length=1023))
