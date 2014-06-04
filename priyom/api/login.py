import binascii
import unicodedata

import sqlalchemy.orm.exc

import teapot
import teapot.forms
import teapot.request

import priyom.model
import priyom.model.user
import priyom.model.saslprep

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

    @teapot.forms.field
    def loginname(self, value):
        if not value:
            raise ValueError("Must not be empty")

        value = str(value)

        try:
            prepped = priyom.model.saslprep.saslprep(
                value,
                allow_unassigned=False)
        except ValueError:
            raise self._loginname_error() from None

        if len(prepped) > priyom.model.User.loginname.type.length:
            raise ValueError("Login name too long")

        return value

    @teapot.forms.field
    def email(self, value):
        if not value:
            raise ValueError("Must not be empty")

        value = str(value)

        if len(value) > priyom.model.User.email.type.length:
            raise ValueError("Email too long")

        return value

    @teapot.forms.field
    def password(self, value):
        if not value:
            raise ValueError("Must not be empty")

        try:
            value = priyom.model.saslprep.saslprep(
                str(value),
                allow_unassigned=False)
        except ValueError:
            raise ValueError("Password is malformed or contains invalid"
                             " characters")

        classes = set(
            unicodedata.category(c)[0]
            for c in value)

        tradeoff = (len(self.required_unicode_major_classes - classes)
                    * self.tradeoff_per_missing_class)

        if len(value) < tradeoff + self.minimum_password_length:
            raise ValueError("Password violates the strength criteria")

        return value

    @teapot.forms.field
    def password_confirm(self, value):
        if not value:
            raise ValueError("Must not be empty")

        try:
            value = priyom.model.saslprep.saslprep(
                str(value),
                allow_unassigned=False)
        except ValueError:
            raise ValueError("Password is malformed or contains invalid"
                             " characters")

        return value

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
    def _login_failed():
        return ValueError("Unknown login name or invalid password")

    @teapot.forms.field
    def loginname(self, value):
        if not value:
            raise ValueError("Must not be empty")
        try:
            value = priyom.model.saslprep.saslprep(
                str(value), allow_unassigned=True)
        except ValueError:
            raise ValueError("Login name is malformed or contains invalid "
                             "characters")
        return value

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
