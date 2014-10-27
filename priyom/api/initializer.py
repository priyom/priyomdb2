import sqlalchemy.orm

import priyom.model

from .auth import Capability

def get_capability(dbsession, key):
    cap = priyom.model.Capability()
    cap.key = key
    dbsession.add(cap)
    return cap

def get_group(dbsession, name):
    group = priyom.model.Group()
    group.name = name
    dbsession.add(group)
    return group

def setup_group(dbsession, name, capabilities):
    group = get_group(dbsession, name)
    group.capabilities.clear()
    for cap in capabilities:
        capobj = get_capability(dbsession, cap)
        group.add_capability(capobj)
    return group

def create_base_data(dbsession):
    admin_user = priyom.model.User("root", "root@api.priyom.org")
    # FIXME: get rid of this!!!
    admin_user.set_password_from_plaintext("admin")
    dbsession.add(admin_user)
    dbsession.commit()

    anon_group = setup_group(
        dbsession,
        priyom.model.Group.ANONYMOUS,
        [
            Capability.VIEW_STATION,
            Capability.VIEW_EVENT
        ])

    registered_group = setup_group(
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

    registered_group.users.append(admin_user)

    unmoderated_group = setup_group(
        dbsession,
        priyom.model.Group.UNMODERATED,
        [
            Capability.LOG_UNMODERATED
        ])

    unmoderated_group.users.append(admin_user)

    mod_group = setup_group(
        dbsession,
        priyom.model.Group.MODERATORS,
        [
            Capability.REVIEW_LOG,

            Capability.CREATE_ALPHABET,
            Capability.EDIT_ALPHABET,
            Capability.DELETE_ALPHABET,

            Capability.CREATE_MODE,
            Capability.EDIT_MODE,
            Capability.DELETE_MODE,

            Capability.VIEW_GROUP,
        ])

    mod_group.users.append(admin_user)

    admin_group = setup_group(
        dbsession,
        priyom.model.Group.ADMINS,
        [
            Capability.CREATE_EVENT,
            Capability.VIEW_EVENT,
            Capability.EDIT_EVENT,
            Capability.DELETE_EVENT,

            Capability.CREATE_FORMAT,
            Capability.VIEW_FORMAT,
            Capability.EDIT_FORMAT,
            Capability.DELETE_FORMAT,

            Capability.CREATE_STATION,
            Capability.VIEW_STATION,
            Capability.EDIT_STATION,
            Capability.DELETE_STATION,

            Capability.CREATE_USER,
            Capability.VIEW_USER,
            Capability.EDIT_USER,
            Capability.DELETE_USER,

            Capability.CREATE_GROUP,
            Capability.VIEW_GROUP,
            Capability.EDIT_GROUP,
            Capability.DELETE_GROUP,
        ])

    admin_group.users.append(admin_user)

    wheel_group = setup_group(
        dbsession,
        priyom.model.Group.WHEEL,
        [
            Capability.ROOT
        ])

    wheel_group.users.append(admin_user)

    unmoderated_group.supergroup = mod_group
    registered_group.supergroup = mod_group
    mod_group.supergroup = admin_group
    admin_group.supergroup = wheel_group

    dbsession.commit()
