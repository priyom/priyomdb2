import logging

import pytz

from sqlalchemy import func
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

@require_capability(Capability.VIEW_GROUP)
@router.route("/group")
@teapot.sqlalchemy.dbview.dbview(teapot.sqlalchemy.dbview.make_form(
    priyom.model.Group,
    [
        ("id", priyom.model.Group.id, None),
        ("name", priyom.model.Group.name, None),
        ("member_count", teapot.sqlalchemy.dbview.subquery(
            priyom.model.user.user_groups,
            func.count('*').label("member_count")
        ).group_by(
            priyom.model.user.user_groups.c.group_id
        ), int)
    ],
    objects="primary, fields",
    default_orderfield="name"))
@xsltea_site.with_template("view_groups.xml")
def view_groups(request: teapot.request.Request, view):
    yield teapot.response.Response(None)

    yield {
        "view": view
    }, {}

def group_users(request, query):
    return query.join(
        priyom.model.user.user_groups,
        priyom.model.user.user_groups.c.user_id == priyom.model.User.id
    ).filter(
        priyom.model.user.user_groups.c.group_id == request.kwargs["group_id"]
    )

@require_capability(Capability.VIEW_GROUP)
@router.route("/group/{group_id:d}")
@teapot.sqlalchemy.dbview.dbview(teapot.sqlalchemy.dbview.make_form(
    priyom.model.User,
    [
        ("id", priyom.model.User.id, None),
        ("loginname", priyom.model.User.loginname, None),
        ("email", priyom.model.User.email, None),
    ],
    objects="primary",
    custom_filter=group_users,
    default_orderfield="loginname"))
@xsltea_site.with_template("group_view.xml")
def view_group(request: teapot.request.Request, group_id, view):
    group = request.dbsession.query(priyom.model.Group).get(group_id)
    if group is None:
        raise teapot.make_error_response(404, "Group not found")

    yield teapot.response.Response(None)
    yield {
        "group": group,
        "view": view
    }, {}

@require_capability(Capability.EDIT_GROUP)
@router.route("/group/{group_id:d}")
@teapot.sqlalchemy.dbview.dbview(teapot.sqlalchemy.dbview.make_form(
    priyom.model.User,
    [
        ("id", priyom.model.User.id, None),
        ("loginname", priyom.model.User.loginname, None),
        ("email", priyom.model.User.email, None),
    ],
    objects="primary",
    custom_filter=group_users,
    default_orderfield="loginname"))
@xsltea_site.with_template("group_form.xml")
def edit_group(request: teapot.request.Request, group_id, view):
    group = request.dbsession.query(priyom.model.Group).get(group_id)
    if group is None:
        raise teapot.make_error_response(404, "Group not found")

    yield teapot.response.Response(None)
    yield {
        "group": group,
        "view": view
    }, {}

def get_group_viewer(request):
    if request.auth.has_capability(Capability.EDIT_GROUP):
        return edit_group
    return view_group
