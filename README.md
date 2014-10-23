priyom.org Database Backend
===========================

This is the source code of the *next generation* of the [priyom.org][0] database
backend server.

The code is still in development and *not deployed live*. Note that it also
contains parts which are inherently and *intendedly* unsafe (such as the default
login of root:admin). These things will change with deployment, but are handy
for local development.

Dependencies
------------

* Python ≥ 3.3
* [sqlalchemy][2] ≥ 0.8
* [alembic][3]
* [teapot with xsltea][1] (recent, i.e. devel branch)
* and probably others :)

Configuring
-----------

Adapt the path in ``app.wsgi`` to point to your check out. Add a
``priyom_config.py`` file with the following settings:

    from priyom.paths import *
    import sys
    sys.path.insert(0, PATH_TO_TEAPOT)
    set_paths(paths(PATH_TO_CHECKOUT))
    database_url = VALID_DATABASE_URL

Where the placeholders need to be replaced according to the following rules:

* ``PATH_TO_TEAPOT`` must be a string pointing to the folder of the teapot
  checkout, that is, where the ``teapot`` and ``xsltea`` directories are found.
* ``PATH_TO_CHECKOUT`` must point to the path of the priyomdb2 checkout.
* ``VALID_DATABASE_URL`` must be a database URL understood by sqlalchemy
  pointing to a database which can be used by priyomdb2.

Setting up a database
---------------------

To set up a fresh database, run ``./utils/create_db.py``. This will use the
configuration to create a fresh database. Note that an existing database is not
deleted, you have to do that yourself. Conflicts between an existing database
and the attempt to create a new database can lead to funny things, don’t beat me
for that.

Upgrading a database
--------------------

Database versioning is handled by [alembic][3]. To upgrade the database to the
most recent version, run:

    python3-alembic upgrade head

Note that on your system, the command may be simply ``alembic`` or something
like that—this depends on how your system handles python3 vs. python2
namespacing. Make sure you run the python3 version of alembic.

Running
-------

To spawn a local webserver serving the API, just call ``./serve.py``. Don’t do
that for production.


   [0]: http://priyom.org
   [1]: https://github.com/zombofant/teapot
   [2]: http://www.sqlalchemy.org/
   [3]: https://bitbucket.org/zzzeek/alembic
