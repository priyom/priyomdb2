import logging
import sqlalchemy.exc

import teapot

import priyom.logic
import priyom.model

from sqlalchemy import func

from .auth import *
from .dbview import *
from .shared import *

def mdzhb_format():
    TF, TFN = priyom.model.TransmissionFormat, priyom.model.TransmissionFormatNode
    call = TFN("[0-9]{2}\s+[0-9]{3}", key="call", comment="“Callsign”")
    callwrap = TFN(
        call,
        duplicity="+",
        separator=" ",
        key="callwrap",
        saved=False,
        comment="Group callsigns separated with space"
    )
    codeword = TFN("\w+",
                   key="codeword",
                   comment="Single word")
    numbers = TFN("([0-9]{2} ){3}[0-9]{2}",
                  key="numbers",
                  comment="Four two-digit numbers")
    messagewrap = TFN(
        TFN(
            codeword,
            TFN(" ", comment="Single space"),
            numbers,
            comment="A single message"
        ),
        duplicity="+",
        separator=" ",
        key="messagewrap",
        saved=False,
        comment="Join message parts"
    )
    tree = TFN(
        callwrap,
        TFN(" ", comment="Single space"),
        messagewrap,
        comment="S28 style message"
    )
    return TF("Example format", tree), callwrap, call, messagewrap, codeword, numbers

@require_capability(Capability.VIEW_FORMAT)
@dbview(priyom.model.TransmissionFormat,
        [
            ("id", priyom.model.TransmissionFormat.id, None),
            ("modified", priyom.model.TransmissionFormat.modified, None),
            ("display_name", priyom.model.TransmissionFormat.display_name, None),
            ("user_count",
             subquery(priyom.model.TransmissionStructuredContents,
                      func.count('*').label("user_count")
                  ).with_labels().group_by(
                      priyom.model.TransmissionStructuredContents.format_id
                  ),
             int)
        ],
        default_orderfield="display_name")
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
        format = mdzhb_format()[0]
    else:
        format = request.dbsession.query(priyom.model.TransmissionFormat).get(
            format_id)

    form = priyom.logic.TransmissionFormatForm.initialize_from_database(
        format)

    yield teapot.response.Response(None)
    yield {
        "form": form,
        "has_users": format.get_has_users()
    }, {}

@require_capability(Capability.EDIT_FORMAT)
@router.route("/format/{format_id:d}/edit",
              methods={teapot.request.Method.POST})
@xsltea_site.with_template("format_form.xml")
def edit_format_POST(request: teapot.request.Request, format_id=0):
    post_data = request.post_data
    dbsession = request.dbsession

    form = priyom.logic.TransmissionFormatForm(
        post_data=post_data)

    target, action = form.find_action(post_data)

    if action == "update":
        pass
    elif action == "add_child":
        target.children.append(priyom.logic.TransmissionFormatRow())
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
            format = dbsession.query(priyom.model.TransmissionFormat).get(
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

    format = request.dbsession.query(priyom.model.TransmissionFormat).get(
        format_id)

    template_args = {
        "form": form,
        "has_users": False if format is None else format.get_has_users()
    }

    yield teapot.response.Response(None)
    yield template_args, {}
