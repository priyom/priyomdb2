import logging

import pytz

import sqlalchemy.exc
import sqlalchemy.orm.exc

import teapot
import teapot.errors
import teapot.forms
import teapot.request

import priyom.model
import priyom.model.user
import priyom.logic.fields

from .auth import *
from .shared import *

class SelfForm(teapot.forms.Form):
    def __init__(self, *, user=None, **kwargs):
        super().__init__(**kwargs)
        if user is not None:
            self.email = user.email
            self.timezone = user.timezone
            self.locale = user.locale

    email = priyom.logic.fields.EmailField()
    password_current = priyom.logic.fields.PasswordVerifyField()
    new_password = priyom.logic.fields.PasswordSetField()
    new_password_confirm = priyom.logic.fields.PasswordConfirmField(
        new_password)
    timezone = priyom.logic.fields.TimezoneField()
    locale = priyom.logic.fields.LocaleField()

    def postvalidate(self, request):
        if not self.password_current or not self.new_password:
            # remove all on password fields errors, if no password change is
            # requested
            self.errors.pop(SelfForm.password_current, None)
            self.errors.pop(SelfForm.new_password, None)
            self.errors.pop(SelfForm.new_password_confirm, None)

        if self.password_current and not self.errors:
            user = request.auth.user
            if not priyom.model.user.verify_password(
                    user.password_verifier,
                    self.password_current):
                teapot.forms.ValidationError(
                    ValueError("Incorrect password"),
                    SelfForm.password_current,
                    self).register()


@require_capability(Capability.EDIT_SELF)
@router.route("/self",
              methods={teapot.request.Method.GET})
@xsltea_site.with_template("self_form.xml")
def edit_self(request: teapot.request.Request):
    user = request.auth.user

    yield teapot.response.Response(None)

    form = SelfForm(user=user)

    yield ({
        "user": user,
        "form": form
    }, {})

@require_capability(Capability.EDIT_SELF)
@router.route("/self",
              methods={teapot.request.Method.POST})
@xsltea_site.with_template("self_form.xml")
def edit_self_POST(request: teapot.request.Request):
    user = request.auth.user

    form = SelfForm(request=request)
    if not form.errors:
        user.email = form.email
        if form.password_current and form.new_password:
            user.set_password_from_plaintext(form.new_password)
        user.timezone = form.timezone
        user.locale = form.locale
        # update localizer :)
        from .shared import textdb
        request.localizer = textdb.get_localizer(
            user.locale,
            pytz.timezone(user.timezone))

        request.dbsession.commit()

        raise teapot.make_redirect_response(request, edit_self)

    yield teapot.response.Response(None)

    yield ({
        "user": user,
        "form": form
    }, {})

@require_capability(Capability.VIEW_USER)
@router.route("/user/{user_id:d}")
@xsltea_site.with_template("user_view.xml")
def view_user(request: teapot.request.Request, user_id):
    user = request.dbsession.query(priyom.model.User).get(user_id)
    if user is None:
        raise teapot.make_error_response(404, "User not found")

    yield teapot.response.Response(None)
    yield ({
        "user": user,
        "recent_events": request.dbsession.query(priyom.model.Event).filter(
            priyom.model.Event.submitter == user
        ).order_by(priyom.model.Event.created.desc()).limit(25)
    }, {})
