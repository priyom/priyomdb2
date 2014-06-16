import binascii
import unicodedata

import sqlalchemy.orm.exc

import teapot
import teapot.forms
import teapot.request

import priyom.model
import priyom.model.user
import priyom.model.saslprep

import priyom.logic.fields

from .auth import *
from .shared import *

from . import dash

fake_verifier = priyom.model.user.create_default_password_verifier(
    b"foo", b"bar")

class SignupForm(teapot.forms.Form):
    required_unicode_major_classes = {
        "L", "N", "S"
    }
    minimum_password_length = 8
    tradeoff_per_missing_class = 8

    @staticmethod
    def _loginname_error():
        return ValueError("Login name is malformed, contains invalid "
                          "characters or is already taken")

    loginname = priyom.logic.fields.LoginNameField()
    email = priyom.logic.fields.EmailField()
    password = priyom.logic.fields.PasswordSetField()
    password_confirm = priyom.logic.fields.PasswordConfirmField(password)

    def postvalidate(self, request):
        dbsession = request.dbsession

        if not self.errors.get(SignupForm.loginname, None):
            try:
                existing_user = dbsession.query(
                    priyom.model.User
                ).filter(
                    priyom.model.User.loginname == self.loginname
                ).one()
            except sqlalchemy.orm.exc.NoResultFound:
                pass
            else:
                teapot.forms.ValidationError(
                    self._loginname_error(),
                    SignupForm.loginname,
                    self).register()

        if (not self.errors.get(SignupForm.password, None)
            and self.password != self.password_confirm):
            teapot.forms.ValidationError(
                "Passwords do not match",
                SignupForm.password_confirm,
                self).register()

@router.route("/signup", methods={teapot.request.Method.GET})
@xsltea_site.with_template("signup.xml")
def signup(request: teapot.request.Request):
    yield teapot.response.Response(None)
    form = SignupForm()
    yield ({
        "signup_form": form,
        "signup": signup
    }, {})

@router.route("/signup", methods={teapot.request.Method.POST})
@xsltea_site.with_variable_template()
def signup_POST(request: teapot.request.Request):
    dbsession = request.dbsession
    form = SignupForm(request=request)

    if not form.errors:
        # we might end up with a duplicate username anyways, due to
        # concurrency. so we do the logic here, so we can add an error later

        anon_group = dbsession.query(
            priyom.model.Group
        ).filter(
            priyom.model.Group.name == priyom.model.Group.REGISTERED
        ).one()

        new_user = priyom.model.user.User(
            form.loginname,
            form.email)
        new_user.set_password_from_plaintext(form.password)

        dbsession.add(new_user)

        try:
            dbsession.commit()
        except sqlalchemy.exc.IntegrityError:
            # user name already taken
            teapot.forms.ValidationError(
                SignupForm._loginname_error(),
                SignupForm.loginname,
                form).register()
            dbsession.rollback()
        else:
            anon_group.add_user(new_user)
            dbsession.commit()

    if form.errors:
        yield "signup.xml"
        yield teapot.response.Response(None)
        yield ({
            "signup_form": form,
            "signup": signup
        }, {})
        return

    yield "signup-success.xml"
    yield teapot.response.Response(None)
    yield ({
        "loginname": form.loginname,
        "login": login
    }, {})


class LoginForm(teapot.forms.Form):
    @staticmethod
    def opaque_error():
        return ValueError("Unknown login name or invalid password")

    loginname = priyom.logic.fields.LoginNameField()
    password = priyom.logic.fields.PasswordVerifyField()

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
                self.opaque_error(),
                LoginForm.loginname,
                self).register()
        else:
            if not priyom.model.user.verify_password(
                    user.password_verifier,
                    self.password):
                teapot.forms.ValidationError(
                    self.opaque_error(),
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
        yield teapot.response.Response(None)
        yield {
            "form": form
        }, {}
        return

    user = form.user

    session = priyom.model.UserSession(user)
    dbsession.add(session)
    dbsession.commit()

    response = teapot.make_redirect_response(request, dash.dash)
    response.cookies["api_session_key"] = binascii.b2a_hex(
        session.session_key).decode()
    response.cookies["api_session_key"]["httponly"] = True

    yield response

@require_login(unauthed_routable=dash.dash)
@router.route("/logout", methods={teapot.request.Method.GET})
def logout(request: teapot.request.Request):
    response = teapot.make_redirect_response(request, dash.dash)
    response.cookies["api_session_key"] = ""
    response.cookies["api_session_key"]["Expires"] = 1
    return response
