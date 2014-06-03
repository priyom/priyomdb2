import sqlalchemy.orm

import priyom.model

from .auth import Capability

def get_capability(dbsession, key):
    try:
        cap = dbsession.query(priyom.model.Capability).filter(
            priyom.model.Capability.key == key).one()
    except sqlalchemy.orm.exc.NoResultFound as err:
        cap = priyom.model.Capability()
        cap.key = key
        dbsession.add(cap)
    return cap

def get_group(dbsession, name):
    try:
        group = dbsession.query(priyom.model.Group).filter(
            priyom.model.Group.name == name).one()
    except sqlalchemy.orm.exc.NoResultFound as err:
        group = priyom.model.Group()
        group.name = name
        dbsession.add(group)
    return group

def setup_group(dbsession, name, capabilities):
    group = get_group(dbsession, name)
    group.capabilities.clear()
    for cap in capabilities:
        capobj = get_capability(dbsession, cap)
        if capobj not in group.capabilities:
            group.add_capability(capobj)
    return group

def create_base_data(dbsession):
    try:
        admin_user = dbsession.query(priyom.model.User).filter(
            priyom.model.User.loginname == "root").one()
    except sqlalchemy.orm.exc.NoResultFound as err:
        admin_user = priyom.model.User("root", "root@api.priyom.org")
        # FIXME: get rid of this!!!
        admin_user.set_password_from_plaintext(
            "admin", priyom.model.user.DEFAULT_ITERATION_COUNT)
        dbsession.add(admin_user)
        dbsession.commit()

    setup_group(
        dbsession,
        priyom.model.Group.ANONYMOUS,
        [
            Capability.VIEW_STATION,
            Capability.VIEW_EVENT
        ])

    group = setup_group(
        dbsession,
        priyom.model.Group.REGISTERED,
        [
            Capability.LOG,
            Capability.EDIT_SELF,
            Capability.VIEW_USER,
            Capability.VIEW_ALPHABET,
            Capability.VIEW_FORMAT,
            Capability.VIEW_MODE,
            Capability.VIEW_GROUP
        ])

    if admin_user not in group.users:
        group.users.append(admin_user)

    group = setup_group(
        dbsession,
        priyom.model.Group.MODERATORS,
        [
            Capability.REVIEW_LOG
        ])

    if admin_user not in group.users:
        group.users.append(admin_user)

    group = setup_group(
        dbsession,
        priyom.model.Group.ADMINS,
        [
            Capability.ROOT
        ])

    if admin_user not in group.users:
        group.users.append(admin_user)



    dbsession.commit()
