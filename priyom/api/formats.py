import logging
import sqlalchemy.exc

import teapot
import teapot.sqlalchemy
import teapot.forms
import teapot.html

import priyom.logic
import priyom.model
import priyom.model.format_parser

from sqlalchemy import func

from .auth import *
from .shared import *

from priyom.model.format_templates import mkformat, monolyth

class FormatForm(teapot.forms.Form):
    display_name = teapot.html.TextField()
    description = teapot.html.TextField()
    format_string = teapot.html.TextField()

    @classmethod
    def instance_from_object(cls, obj):
        instance = cls()
        instance.display_name = obj.display_name
        instance.description = obj.description
        instance.format_string = obj.root_node.to_parser_expression()
        instance.format_tree = obj.root_node
        return instance

    def to_database_object(self, destination=None):
        if destination is None:
            return priyom.model.Format(
                self.display_name,
                self.format_tree,
                description=self.description)
        else:
            destination.display_name = self.display_name
            destination.root_node = self.format_tree
            destination.description = self.description
            return destination

    def postvalidate(self, request):
        try:
            self.format_tree = priyom.model.format_parser.parse_string(self.format_string)
        except UnicodeEncodeError as err:
            teapot.forms.ValidationError(
                ValueError("Unsupported character at position {}: {!r}", err.start, err.object[err.start:err.end]),
                FormatForm.format_string,
                self).register()
        except priyom.model.format_parser.SyntaxError as err:
            msg = err.message
            teapot.forms.ValidationError(
                ValueError("Syntax error: {}:{}: {}", err.position.line0, err.position.col0,
                           msg),
                FormatForm.format_string,
                self).register()

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

    form = FormatForm.instance_from_object(fmt)

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

    form = FormatForm(request=request)

    target, action = form.find_action(request.post_data)

    if action == "update":
        pass
    elif action in {"save_to_db", "save_copy"}:
        if action == "save_to_db":
            format = dbsession.query(priyom.model.Format).get(
                format_id)
            if format and format.get_has_users():
                teapot.forms.ValidationError(
                    ValueError("Cannot save: This format currently has users"),
                    None,
                    form).register()
        else:
            format = None

        if not form.errors:
            try:
                format = form.to_database_object(destination=format)
                dbsession.add(format)
                dbsession.commit()
            except sqlalchemy.exc.IntegrityError as err:
                dbsession.rollback()
                teapot.forms.ValidationError(
                    ValueError(str(err)),
                    None,
                    form).register()
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
