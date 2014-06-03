import binascii

import sqlalchemy.orm.exc

import teapot
import teapot.forms
import teapot.request

import priyom.model

from .auth import *
from .shared import *

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
            teapot.forms.ValidationError(
                error_msg,
                LoginForm.loginname,
                form).register()

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

    from . import dash
    response = teapot.make_redirect_response(request, dash.dash)
    response.cookies["api_session_key"] = binascii.b2a_hex(
        session.session_key).decode()
    response.cookies["api_session_key"]["httponly"] = True

    yield response

@require_login()
@router.route("/logout", methods={teapot.request.Method.GET})
def logout(request: teapot.request.Request):
    from .dash import dash
    response = teapot.make_redirect_response(request, dash)
    response.cookies["api_session_key"] = ""
    response.cookies["api_session_key"]["Expires"] = 1
    return response
