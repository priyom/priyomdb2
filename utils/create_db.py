#!/usr/bin/python3
if __name__ == "__main__":
    import os

    import util_helpers
    parser = util_helpers.default_argparser()

    args = parser.parse_args()

    util_helpers.setup_env(args)

    import priyom.config
    import priyom.api.initializer

    import sqlalchemy

    import alembic
    import alembic.config

    dbengine = sqlalchemy.create_engine(
        priyom.config.database_url,
        echo=False,
        encoding="utf8",
        convert_unicode=True)
    priyom.model.Base.metadata.create_all(dbengine)
    dbsession = sqlalchemy.orm.sessionmaker(bind=dbengine)()

    alembic_cfg = alembic.config.Config(
        os.path.join(priyom.config.get_code_path(), "alembic.ini")
    )

    alembic.command.stamp(alembic_cfg, "head")

    priyom.api.initializer.create_base_data(dbsession)
    rootuser = dbsession.query(priyom.model.User).filter(
        priyom.model.User.loginname == "root").one()
