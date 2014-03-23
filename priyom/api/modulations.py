import teapot.request

import priyom.model

from .auth import *
from .shared import *
from .pagination import *

class ModulationForm(teapot.forms.Form):
    @teapot.forms.field
    def display_name(self, value):
        if not value:
            raise ValueError("Must not be empty")
        return value

@require_capability("admin")
@paginate(priyom.model.Modulation,
          25,
          ("display_name", "asc"),
          "page")
@router.route("/modulation", order=0, methods={teapot.request.Method.GET})
@xsltea_site.with_template("view_modulations.xml")
def view_modulations(request: teapot.request.Request, page):
    modulations = list(page)

    yield teapot.response.Response(None)

    yield {
        "modulations": modulations,
        "page": page,
        "view_modulations": view_modulations,
        "form": ModulationForm()
    }, {}

@require_capability("admin")
@paginate(priyom.model.Modulation,
          25,
          ("display_name", "asc"),
          "page")
@router.route("/modulation", order=0, methods={teapot.request.Method.POST})
@xsltea_site.with_template("view_modulations.xml")
def view_modulations_POST(request: teapot.request.Request, page):
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
            page=page)

    modulations = list(page)
    yield teapot.response.Response(None)

    yield {
        "modulations": modulations,
        "page": page,
        "view_modulations": view_modulations,
        "form": form
    }, {}
