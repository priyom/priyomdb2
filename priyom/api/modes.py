import sqlalchemy.exc

import teapot.html
import teapot.request
import teapot.sqlalchemy

import priyom.model

from sqlalchemy import func

from .auth import *
from .shared import *

class ModeForm(teapot.forms.Form):
    display_name = teapot.html.TextField()

@require_capability(Capability.VIEW_MODE)
@teapot.sqlalchemy.dbview.dbview(teapot.sqlalchemy.dbview.make_form(
    priyom.model.Mode,
    [
        ("id", priyom.model.Mode.id, None),
        ("display_name", priyom.model.Mode.display_name, None),
        ("user_count",
         teapot.sqlalchemy.dbview.subquery(
             priyom.model.EventFrequency, func.count('*').label("user_count")
         ).group_by(
             priyom.model.EventFrequency.mode_id
         ),
         int)
    ],
    itemsperpage=25,
    default_orderfield="display_name"))
@router.route("/mode", order=0, methods={teapot.request.Method.GET})
@xsltea_site.with_template("view_modes.xml")
def view_modes(request: teapot.request.Request, view):
    modes = list(view)

    yield teapot.response.Response(None)

    yield {
        "modes": modes,
        "view": view,
        "view_modes": view_modes,
        "edit_mode": edit_mode,
        "delete_mode": delete_mode_POST,
        "form": ModeForm()
    }, {}

@require_capability(Capability.EDIT_MODE)
@router.route("/mode/{mode_id:d}/edit",
              order=0,
              methods={teapot.request.Method.GET})
@xsltea_site.with_template("mode_form.xml")
def edit_mode(request: teapot.request.Request, mode_id=0):
    form = ModeForm()
    existing = request.dbsession.query(
        priyom.model.Mode
    ).get(mode_id)
    if existing is not None:
        form.display_name = existing.display_name

    yield teapot.response.Response(None)
    yield {
        "mode_id": mode_id,
        "form": form
    }, {}

@require_capability(Capability.EDIT_MODE)
@router.route("/mode/{mode_id:d}/edit",
              order=0,
              methods={teapot.request.Method.POST})
@xsltea_site.with_template("mode_form.xml")
def edit_mode_POST(request: teapot.request.Request, mode_id=0):
    form = ModeForm(request=request)

    if not form.errors:
        dbsession = request.dbsession
        existing = dbsession.query(
            priyom.model.Mode
        ).get(mode_id)
        try:
            if existing is None:
                existing = priyom.model.Mode(form.display_name)
            else:
                existing.display_name = form.display_name
            dbsession.add(existing)
            dbsession.commit()
        except sqlalchemy.exc.IntegrityError:
            dbsession.rollback()
            teapot.forms.ValidationError(
                "Display name must be unique",
                ModeForm.display_name,
                form).register()
        else:
            raise teapot.response.make_redirect_response(
                request,
                view_modes)

    yield teapot.response.Response(None)
    yield {
        "mode_id": mode_id,
        "form": form
    }, {}

@require_capability(Capability.DELETE_MODE)
@router.route("/mode/{mode_id:d}/delete",
              order=0,
              methods={teapot.request.Method.POST,
                       teapot.request.Method.GET})
@xsltea_site.with_template("mode_delete.xml")
def delete_mode_POST(request: teapot.request.Request,
                           mode_id=0):
    form = teapot.forms.Form()
    if request.method == teapot.request.Method.POST:
        dbsession = request.dbsession
        existing = dbsession.query(
            priyom.model.Mode
        ).get(
            mode_id
        )

        if existing is not None:
            try:
                dbsession.delete(existing)
                dbsession.commit()
            except sqlalchemy.exc.IntegrityError:
                dbsession.rollback()
                teapot.forms.ValidationError(
                    "This mode is still in use",
                    None,
                    form).register()
            else:
                raise teapot.response.make_redirect_response(
                    request,
                    view_modes)
        else:
            teapot.forms.ValidationError(
                "This mode does not exist",
                None,
                form).register()

    yield teapot.response.Response(None)
    yield {
        "form": form,
        "mode_id": mode_id
    }, {}
