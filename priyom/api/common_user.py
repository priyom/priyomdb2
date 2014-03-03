import teapot
import teapot.request

import priyom.model

from .shared import *
from .auth import *
from .pagination import *

@require_login()
@router.route("/", methods={teapot.request.Method.GET})
@xsltea_site.with_template("dash.xml")
def dash(request: teapot.request.Request):
    yield teapot.response.Response(None)
    transform_args = {
        "version": "devel"
    }
    template_args = dict(transform_args)
    template_args["auth"] = request.auth
    yield (template_args, transform_args)

@require_login()
@router.route("/logout", methods={teapot.request.Method.GET})
def logout(request: teapot.request.Request):
    from .anonymous_user import anonhome
    response = teapot.make_redirect_response(request, anonhome)
    response.cookies["api_session_key"] = ""
    response.cookies["api_session_key"]["Expires"] = 1
    return response

@paginate(priyom.model.Station,
          25,
          ("enigma_id", "asc"),
          "page")
@router.route("/station", methods={teapot.request.Method.GET})
@xsltea_site.with_template("view_stations.xml")
def view_stations(page):
    stations = list(page)

    yield teapot.response.Response(
        None,
        last_modified=max(
            station.modified
            for station in stations))

    from .admin_user import edit_station, delete_station

    yield {
        "stations": stations,
        "view_stations": view_stations,
        "edit_station": edit_station,
        "delete_station": delete_station,
        "page": page
    }, {}
