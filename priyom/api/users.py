import logging

import sqlalchemy.exc
import sqlalchemy.orm.exc

import teapot
import teapot.errors
import teapot.forms
import teapot.request

import priyom.model

from .auth import *
from .dbview import *
from .shared import *

class SelfForm(teapot.forms.Form):
    def __init__(self, *, user=None, **kwargs):
        super().__init__(**kwargs)
        if user is not None:
            self.email = user.email

    @teapot.forms.field
    def email(self, value):
        if not value:
            raise ValueError("Must not be empty")

        value = str(value)

        if len(value) > priyom.model.User.email.type.length:
            raise ValueError("Email too long")

        return value

    @teapot.forms.field
    def password_current(self, value):
        return str(value)

    @teapot.forms.field
    def password(self, value):
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
        try:
            value = priyom.model.saslprep.saslprep(
                str(value),
                allow_unassigned=False)
        except ValueError:
            raise ValueError("Password is malformed or contains invalid"
                             " characters")

        return value

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
