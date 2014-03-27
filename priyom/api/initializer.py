import sqlalchemy.orm

import priyom.model

def get_capability(dbsession, key):
    try:
        cap = dbsession.query(priyom.model.Capability).filter(
            priyom.model.Capability.key == key).one()
    except sqlalchemy.orm.exc.NoResultFound as err:
        cap = priyom.model.Capability()
        cap.key = key
        dbsession.add(cap)
    return cap

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

    mod_cap = get_capability(dbsession, "moderator")
    admin_user.capabilities.append(mod_cap)
    admin_cap = get_capability(dbsession, "admin")
    admin_user.capabilities.append(admin_cap)

    dbsession.commit()
