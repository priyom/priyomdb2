import binascii

import sqlalchemy.orm.exc

import teapot
import teapot.request

import priyom.model

from .shared import *

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
    yield ({}, {})

@teapot.postarg("name", "loginname")
@teapot.postarg("password", "password")
@router.route("/login", methods={teapot.request.Method.POST}, order=1)
@xsltea_site.with_template("login.xml")
def login_POST(loginname, password, request: teapot.request.Request):
    error = False
    error_msg = None
    try:
        user = dbsession.query(
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
        yield (
            {
                "error": error_msg
            },
            {})

    session = priyom.model.UserSession(user)
    dbsession.add(session)
    dbsession.commit()

    from .common_user import dash
    response = teapot.make_redirect_response(request, dash)
    response.cookies["api_session_key"] = binascii.b2a_hex(
        session.session_key).decode()
    response.cookies["api_session_key"]["httponly"] = True

    yield response
