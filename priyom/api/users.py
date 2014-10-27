import logging

import pytz

import sqlalchemy.exc
import sqlalchemy.orm.exc

import teapot
import teapot.errors
import teapot.forms
import teapot.request
import teapot.html

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

@require_capability(Capability.EDIT_USER)
@teapot.sqlalchemy.dbview.dbview(teapot.sqlalchemy.dbview.make_form(
    priyom.model.User,
    [
        ("id", priyom.model.User.id, None),
        ("modified", priyom.model.User.modified, None),
        ("loginname", priyom.model.User.loginname, None),
        ("email", priyom.model.User.email, None)
    ],
    objects="primary",
    default_orderfield="loginname"))
@router.route("/user")
@xsltea_site.with_template("view_users.xml")
def view_users(request: teapot.request.Request, view):
    yield teapot.response.Response(None)

    yield {
        "view": view,
    }, {}

class UserForm(teapot.forms.Form):
    loginname = priyom.logic.fields.LoginNameField()
    email = priyom.logic.fields.EmailField()
    timezone = priyom.logic.fields.TimezoneField()
    locale = priyom.logic.fields.LocaleField()
    groups = priyom.logic.fields.GroupsField()

    def __init__(self, from_user=None, **kwargs):
        super().__init__(**kwargs)
        if from_user:
            self.loginname = from_user.loginname
            self.email = from_user.email
            self.timezone = from_user.timezone
            self.locale = from_user.locale
            self.groups = set(
                group.id
                for group
                in from_user.groups
            )


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

@require_capability(Capability.EDIT_USER)
@router.route("/user/{user_id:d}/edit", methods={teapot.request.Method.GET})
@xsltea_site.with_template("user_form.xml")
def edit_user(request: teapot.request.Request, user_id):
    user = request.dbsession.query(priyom.model.User).get(user_id)
    if user is None:
        raise teapot.make_error_response(404, "User not found")

    form = UserForm(from_user=user)
    yield teapot.response.Response(None)
    yield ({
        "form": form,
        "user": user,
        "recent_events": request.dbsession.query(priyom.model.Event).filter(
            priyom.model.Event.submitter == user
        ).order_by(priyom.model.Event.created.desc()).limit(25)
    }, {})

@require_capability(Capability.EDIT_USER)
@router.route("/user/{user_id:d}/edit", methods={teapot.request.Method.POST})
@xsltea_site.with_template("user_form.xml")
def edit_user_POST(request: teapot.request.Request, user_id):
    user = request.dbsession.query(priyom.model.User).get(user_id)
    if user is None:
        raise teapot.make_error_response(404, "User not found")

    form = UserForm(request=request)

    editor_groups = request.auth.user.groups

    subject_current_group_ids = set(group.id for group in user.groups)
    subject_new_group_ids = form.groups

    departing_groups = [request.dbsession.query(priyom.model.Group).get(group_id)
                        for group_id
                        in subject_current_group_ids - subject_new_group_ids]
    for group in departing_groups:
        if not any(group.is_subgroup_of(editor_group)
                   for editor_group in editor_groups):
            teapot.forms.ValidationError(
                PermissionError(
                    "You cannot remove members from the group `{}'",
                    request.localizer(group.name, ctxt="group")),
                UserForm.groups,
                form).register()

    joining_groups = [request.dbsession.query(priyom.model.Group).get(group_id)
                      for group_id
                      in subject_new_group_ids - subject_current_group_ids]
    for group in joining_groups:
        if not any(group == editor_group or group.is_subgroup_of(editor_group)
                   for editor_group in editor_groups):
            teapot.forms.ValidationError(
                PermissionError(
                    "You cannot add members to the group `{}'",
                    request.localizer(group.name, ctxt="group")),
                UserForm.groups,
                form).register()

    if not form.errors:
        for group in departing_groups:
            user.groups.remove(group)
        for group in joining_groups:
            user.groups.append(group)
        user.email = form.email
        user.timezone = form.timezone
        user.locale = form.locale
        request.dbsession.commit()

        raise teapot.make_redirect_response(request, edit_user, user_id=user_id)

    yield teapot.response.Response(None)
    yield ({
        "form": form,
        "user": user,
        "recent_events": request.dbsession.query(priyom.model.Event).filter(
            priyom.model.Event.submitter == user
        ).order_by(priyom.model.Event.created.desc()).limit(25)
    }, {})


def get_user_viewer(request):
    if request.auth.has_capability(Capability.EDIT_USER):
        return edit_user
    else:
        return view_user
