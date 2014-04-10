import sqlalchemy.exc

import teapot.request

import priyom.model

from sqlalchemy import func

from .auth import *
from .dbview import *
from .shared import *

class ModulationForm(teapot.forms.Form):
    @teapot.forms.field
    def display_name(self, value):
        if not value:
            raise ValueError("Must not be empty")
        return value

@require_capability("admin")
@dbview(priyom.model.Modulation,
        [
            ("id", priyom.model.Modulation.id, None),
            ("display_name", priyom.model.Modulation.display_name, None),
            ("user_count",
             subquery(priyom.model.EventFrequency, func.count('*').label("user_count")
                  ).group_by(
                      priyom.model.EventFrequency.modulation_id),
             int)
        ],
        itemsperpage=25,
        default_orderfield="display_name")
@router.route("/modulation", order=0, methods={teapot.request.Method.GET})
@xsltea_site.with_template("view_modulations.xml")
def view_modulations(request: teapot.request.Request, view):
    modulations = list(view)

    yield teapot.response.Response(None)

    yield {
        "modulations": modulations,
        "view": view,
        "view_modulations": view_modulations,
        "edit_modulation": edit_modulation,
        "delete_modulation": delete_modulation_POST,
        "form": ModulationForm()
    }, {}

@require_capability("admin")
@router.route("/modulation/{modulation_id:d}/edit",
              order=0,
              methods={teapot.request.Method.GET})
@xsltea_site.with_template("modulation_form.xml")
def edit_modulation(request: teapot.request.Request, modulation_id=0):
    form = ModulationForm()
    existing = request.dbsession.query(
        priyom.model.Modulation
    ).get(modulation_id)
    if existing is not None:
        form.display_name = existing.display_name

    yield teapot.response.Response(None)
    yield {
        "modulation_id": modulation_id,
        "form": form
    }, {}

@require_capability("admin")
@router.route("/modulation/{modulation_id:d}/edit",
              order=0,
              methods={teapot.request.Method.POST})
@xsltea_site.with_template("modulation_form.xml")
def edit_modulation_POST(request: teapot.request.Request, modulation_id=0):
    form = ModulationForm(request=request)

    if not form.errors:
        dbsession = request.dbsession
        existing = dbsession.query(
            priyom.model.Modulation
        ).get(modulation_id)
        try:
            if existing is None:
                existing = priyom.model.Modulation(form.display_name)
            else:
                existing.display_name = form.display_name
            dbsession.add(existing)
            dbsession.commit()
        except sqlalchemy.exc.IntegrityError:
            dbsession.rollback()
            teapot.forms.ValidationError(
                "Display name must be unique",
                ModulationForm.display_name,
                form).register()
        else:
            raise teapot.response.make_redirect_response(
                request,
                view_modulations)

    yield teapot.response.Response(None)
    yield {
        "modulation_id": modulation_id,
        "form": form
    }, {}

@require_capability("admin")
@router.route("/modulation/{modulation_id:d}/delete",
              order=0,
              methods={teapot.request.Method.POST,
                       teapot.request.Method.GET})
@xsltea_site.with_template("modulation_delete.xml")
def delete_modulation_POST(request: teapot.request.Request,
                           modulation_id=0):
    form = teapot.forms.Form()
    if request.method == teapot.request.Method.POST:
        dbsession = request.dbsession
        existing = dbsession.query(
            priyom.model.Modulation
        ).get(
            modulation_id
        )

        if existing is not None:
            try:
                dbsession.delete(existing)
                dbsession.commit()
            except sqlalchemy.exc.IntegrityError:
                dbsession.rollback()
                teapot.forms.ValidationError(
                    "This modulation is still in use",
                    None,
                    form).register()
            else:
                raise teapot.response.make_redirect_response(
                    request,
                    view_modulations)
        else:
            teapot.forms.ValidationError(
                "This modulation does not exist",
                None,
                form).register()

    yield teapot.response.Response(None)
    yield {
        "form": form,
        "modulation_id": modulation_id
    }, {}
