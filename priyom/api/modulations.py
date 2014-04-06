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
        "form": ModulationForm()
    }, {}

@require_capability("admin")
@dbview(priyom.model.Modulation,
        [
            ("id", priyom.model.Modulation.id, None),
            ("display_name", priyom.model.Modulation.display_name, None),
            ("user_count",
             subquery(priyom.model.EventFrequency,
                      func.count('*').label("user_count")
                  ).group_by(
                      priyom.model.EventFrequency.modulation_id),
             int)
        ],
        itemsperpage=25,
        default_orderfield="display_name")
@router.route("/modulation", order=0, methods={teapot.request.Method.POST})
@xsltea_site.with_template("view_modulations.xml")
def view_modulations_POST(request: teapot.request.Request, view):
    form = ModulationForm(request=request)
    if not form.errors:
        new_modulation = priyom.model.Modulation(
            form.display_name)
        dbsession = request.dbsession
        dbsession.add(new_modulation)
        dbsession.commit()
        raise teapot.make_redirect_response(
            request,
            view_modulations,
            view=view)

    yield teapot.response.Response(None)

    yield {
        "modulations": modulations,
        "view": view,
        "view_modulations": view_modulations,
        "form": form
    }, {}
