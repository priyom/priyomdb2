import logging

import sqlalchemy.exc
import sqlalchemy.orm.exc

import teapot
import teapot.errors
import teapot.forms
import teapot.request

import priyom.model
import priyom.logic.fields

from .auth import *
from .dbview import *
from .shared import *

class SelfForm(teapot.forms.Form):
    def __init__(self, *, user=None, **kwargs):
        super().__init__(**kwargs)
        if user is not None:
            self.email = user.email

    email = priyom.logic.fields.EmailField()
    password_current = priyom.logic.fields.PasswordVerifyField()
    new_password = priyom.logic.fields.PasswordSetField()
    new_password_confirm = priyom.logic.fields.PasswordConfirmField(
        new_password)

    def postvalidate(self, request):
        if not self.password_current or not self.new_password:
            # remove all on password fields errors, if no password change is
            # requested
            self.errors.pop(SelfForm.password_current, None)
            self.errors.pop(SelfForm.new_password, None)
            self.errors.pop(SelfForm.new_password_confirm, None)

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
def edit_self(request: teapot.request.Request):
    user = request.auth.user

    yield teapot.response.Response(None)

    form = SelfForm(request=request)

    yield ({
        "user": user,
        "form": form
    }, {})
