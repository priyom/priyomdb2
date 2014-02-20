import sqlalchemy
import sqlalchemy.orm

import teapot
import teapot.request
import teapot.routing
import teapot.templating

import xsltea

import priyom.model
import priyom.model.user

xsltea_pipeline = xsltea.make_pipeline(
    teapot.templating.FileSystemSource(
        "/var/www/docroot/horazont/projects/priyomdb2/resources/templates/")
)
xsltea_pipeline.loader.add_processor(xsltea.ForeachProcessor)
xsltea_pipeline.loader.add_processor(xsltea.ExecProcessor)

class API(metaclass=teapot.RoutableMeta):
    def __init__(self, database):
        super().__init__()
        self._engine = sqlalchemy.create_engine(
            database,
            echo=False,
            encoding="utf8",
            convert_unicode=True)
        priyom.model.Base.metadata.create_all(self._engine)
        self._session = sqlalchemy.orm.sessionmaker(bind=self._engine)()

        self.create_test_data()

    def create_test_data(self):
        try:
            station = self._session.query(priyom.model.Station).filter(
                priyom.model.Station.enigma_id == "S28").one()
        except sqlalchemy.orm.exc.NoResultFound as err:
            station = priyom.model.Station("S28", None)
            self._session.add(station)
        station.nickname = "The Buzzer"
        station.description = "Buzz buzz buzz"
        station.status = "active"
        station.location = "Right behind ... YOU!"
        self._session.commit()

        try:
            admin_user = self._session.query(priyom.model.User).filter(
                priyom.model.User.loginname == "root").one()
        except sqlalchemy.orm.exc.NoResultFound as err:
            admin_user = priyom.model.User("root", "root@api.priyom.org")
            # FIXME: get rid of this!!!
            admin_user.set_password_from_plaintext(
                "admin", priyom.model.user.DEFAULT_ITERATION_COUNT)
            self._session.add(admin_user)
            self._session.commit()

    @teapot.route("/", methods={teapot.request.Method.GET})
    @xsltea_pipeline.with_template("index.xml")
    def index(self):
        yield teapot.response.Response(None)
        yield {
            "version": "devel"
        }

    @teapot.route("/login", methods={teapot.request.Method.GET})
    @xsltea_pipeline.with_template("login.xml")
    def login_GET(self):
        yield teapot.response.Response(None)
        yield {}

    @teapot.postarg("name", "loginname")
    @teapot.postarg("password", "password")
    @teapot.route("/login", methods={teapot.request.Method.POST})
    @xsltea_pipeline.with_template("login.xml")
    def login_POST(self, loginname, password):
        error = False
        error_msg = None
        try:
            user, _ = self._session.query(
                priyom.model.User).filter(
                    priyom.model.User.loginname == loginname).one()
            print(user)
            if not priyom.model.user.verify_password(
                    user.password_verifier,
                    password):
                error = True
        except sqlalchemy.orm.exc.NoResultFound as err:
            error = True
        except (LookupError, ValueError) as err:
            error = True
            # FIXME: stop leaking information about the existing user here, even
            # if it is broken
            error_msg = "Internal authentication error"

        if error:
            if error_msg is None:
                error_msg = "Unknown user name or invalid password"
            yield teapot.response.Response(None, response_code=401)
            yield {
                "error": error_msg
            }

        session = priyom.model.UserSession(user)
        self._session.add(session)

        # FIXME: login!
        yield teapot.response.Response(None)
        yield {
            "error": "success"
        }


    @teapot.route("/station/{station_id:d}",
                  methods={teapot.request.Method.GET})
    @xsltea_pipeline.with_template("station.xml")
    def station(self, station_id):
        try:
            station = self._session.query(priyom.model.Station).filter(
                priyom.model.Station.id == station_id).one()
        except sqlalchemy.orm.exc.NoResultFound as err:
            raise teapot.errors.make_response_error(
                404, "station not found: #{}".format(station_id))
        yield teapot.response.Response(None)
        yield {
            "station_id": station_id,
            "station": station
        }

class Router(teapot.routing.Router):
    def __init__(self, *args, **kwargs):
        self._api = API(*args, **kwargs)
        super().__init__(self._api)
