import binascii

import sqlalchemy.orm.exc

import teapot
import teapot.forms
import teapot.request

import priyom.model

from .shared import *
from .pagination import *

class LoginForm(teapot.forms.Form):
    @teapot.forms.field
    def loginname(self, value):
        if not value:
            raise ValueError("Must not be empty")
        return str(value)

    @teapot.forms.field
    def password(self, value):
        if not value:
            raise ValueError("Must not be empty")
        return str(value)

@router.route("/", methods={teapot.request.Method.GET}, order=0)
@xsltea_site.with_template("home.xml")
def anonhome(request: teapot.request.Request):
    yield teapot.response.Response(None)
    transform_args = {
        "version": "devel"
    }
    template_args = dict(transform_args)
    yield (template_args, transform_args)

@router.route("/login", methods={teapot.request.Method.GET}, order=1)
@xsltea_site.with_template("login.xml")
def login():
    yield teapot.response.Response(None)
    form = LoginForm()
    yield ({
        "form": form
    }, {})

@router.route("/login", methods={teapot.request.Method.POST}, order=1)
@xsltea_site.with_template("login.xml")
def login_POST(request: teapot.request.Request):
    dbsession = request.dbsession
    form = LoginForm(post_data=request.post_data)
    if not form.errors:
        error = False
        error_msg = None
        try:
            user = dbsession.query(
                priyom.model.User).filter(
                    priyom.model.User.loginname == form.loginname).one()
            if not priyom.model.user.verify_password(
                    user.password_verifier,
                    form.password):
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
            form.errors[LoginForm.loginname] = error_msg

    if form.errors:
        del form.password
        yield teapot.response.Response(None)
        yield {
            "form": form
        }, {}
        return

    session = priyom.model.UserSession(user)
    dbsession.add(session)
    dbsession.commit()

    from .common_user import dash
    response = teapot.make_redirect_response(request, dash)
    response.cookies["api_session_key"] = binascii.b2a_hex(
        session.session_key).decode()
    response.cookies["api_session_key"]["httponly"] = True

    yield response

@paginate(priyom.model.Station,
          25,
          ("enigma_id", "asc"),
          "page")
@router.route("/station", methods={teapot.request.Method.GET})
@xsltea_site.with_template("view_stations.xml")
def view_stations(request:teapot.request.Request, page):
    stations = list(page)

    yield teapot.response.Response(
        None,
        last_modified=max(
            station.modified
            for station in stations))

    from .admin_user import edit_station, delete_station

    yield {
        "stations": stations,
        "view_stations": view_stations,
        "view_station": edit_station if request.auth else view_station,
        "delete_station": delete_station if request.auth else None,
        "page": page
    }, {}

@router.route("/station/{station_id:d}",
              methods={teapot.request.Method.GET})
@xsltea_site.with_variable_template()
def view_station(request: teapot.request.Request, station_id):
    station = request.dbsession.query(priyom.model.Station).get(station_id)

    yield ("station_view.xml" if station else "station_not_found.xml")

    yield teapot.response.Response(
        None,
        response_code=200 if station else 404,
        last_modified=station.modified if station else None)

    if station:
        yield {
            "station": station
        }, {}

    else:
        yield {
            "station_id": station_id
        }, {}
