import binascii

import sqlalchemy.orm.exc

import teapot
import teapot.forms
import teapot.request

import priyom.model
import priyom.model.user
import priyom.model.saslprep

from .auth import *
from .shared import *

fake_verifier = priyom.model.user.create_default_password_verifier(
    b"foo", b"bar")

 
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

    def postvalidate(self, request):
        dbsession = request.dbsession
        try:
            user = dbsession.query(
                priyom.model.User
            ).filter(
                priyom.model.User.loginname == self.loginname
            ).one()
        except (sqlalchemy.orm.exc.NoResultFound, LookupError, ValueError):
            user = None
            # do a fake validation here, to avoid timing attacks
            priyom.model.user.verify_password(
                fake_verifier,
                self.password)
            teapot.forms.ValidationError(
                self._login_failed(),
                LoginForm.loginname,
                self).register()
        else:
            if not priyom.model.user.verify_password(
                    user.password_verifier,
                    self.password):
                teapot.forms.ValidationError(
                    self._login_failed(),
                    LoginForm.loginname,
                    self).register()

        if self.errors:
            user = None

        self.user = user


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
    form = LoginForm(request=request)

    if form.errors:
        del form.password
        yield teapot.response.Response(None)
        yield {
            "form": form
        }, {}
        return

    user = form.user

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
