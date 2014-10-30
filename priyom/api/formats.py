import logging
import sqlalchemy.exc

import teapot
import teapot.sqlalchemy

import priyom.logic
import priyom.model

from sqlalchemy import func

from .auth import *
from .shared import *

from priyom.model.format_templates import mkformat, monolyth

@require_capability(Capability.VIEW_FORMAT)
@teapot.sqlalchemy.dbview.dbview(teapot.sqlalchemy.dbview.make_form(
    priyom.model.Format,
    [
        ("id", priyom.model.Format.id, None),
        ("modified", priyom.model.Format.modified, None),
        ("display_name", priyom.model.Format.display_name, None),
        ("user_count",
         teapot.sqlalchemy.dbview.subquery(
             priyom.model.StructuredContents,
             func.count('*').label("user_count")
         ).with_labels().group_by(
             priyom.model.StructuredContents.format_id
         ),
         int)
    ],
    default_orderfield="display_name"))
@router.route("/format", order=0)
@xsltea_site.with_template("view_formats.xml")
def view_formats(request: teapot.request.Request, view):
    formats = list(view)

    yield teapot.response.Response(None)
    yield {
        "formats": formats,
        "view_formats": view_formats,
        "add_format": edit_format,
        "edit_format": edit_format,
        "view": view,
    }, {}

@require_capability(Capability.EDIT_FORMAT)
@router.route("/format/{format_id:d}/edit",
              methods={teapot.request.Method.GET}, order=0)
@xsltea_site.with_template("format_form.xml")
def edit_format(request: teapot.request.Request, format_id=0):
    if format_id == 0:
        fmt = mkformat(monolyth()[0])
        fmt.display_name = "Example format (monolyth style)"
        fmt.description = "Change me"
    else:
        fmt = request.dbsession.query(priyom.model.Format).get(format_id)

    form = priyom.logic.FormatForm.instance_from_object(fmt)

    yield teapot.response.Response(None)
    yield {
        "form": form,
        "has_users": fmt.get_has_users()
    }, {}

@require_capability(Capability.EDIT_FORMAT)
@router.route("/format/{format_id:d}/edit",
              methods={teapot.request.Method.POST})
@xsltea_site.with_template("format_form.xml")
def edit_format_POST(request: teapot.request.Request, format_id=0):
    post_data = request.post_data
    dbsession = request.dbsession

    form = priyom.logic.FormatForm(
        post_data=post_data)

    target, action = form.find_action(post_data)

    if action == "update":
        pass
    elif action == "add_child":
        target.children.append(priyom.logic.FormatRow())
    elif hasattr(target, "parent") and target.parent:
        if action == "move_up":
            i = target.index
            l = target.parent
            if i >= 1:
                l.pop(i)
                l.insert(i-1, target)
        elif action == "move_down":
            i = target.index
            l = target.parent
            if i < len(l):
                l.pop(i)
                l.insert(i+1, target)
        elif action == "delete":
            del target.parent[target.index]
    elif not form.errors and action in {"save_to_db", "save_copy"}:
        if action == "save_to_db":
            format = dbsession.query(priyom.model.Format).get(
                format_id)
            if format and format.get_has_users():
                raise ValueError("It is not allowed to modify a format with users")
        else:
            format = None

        try:
            format = form.to_database_object(destination=format)
            dbsession.add(format)
            dbsession.commit()
        except sqlalchemy.exc.IntegrityError as err:
            dbsession.rollback()
            logging.error(err)
        else:
            raise teapot.make_redirect_response(
                request,
                edit_format,
                format_id=format.id)

    format = request.dbsession.query(priyom.model.Format).get(
        format_id)

    template_args = {
        "form": form,
        "has_users": False if format is None else format.get_has_users()
    }

    yield teapot.response.Response(None)
    yield template_args, {}
