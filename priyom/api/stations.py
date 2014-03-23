import teapot

import priyom.model

from .auth import *
from .pagination import *
from .shared import *

@paginate(priyom.model.Station,
          25,
          ("enigma_id", "asc"),
          "page")
@router.route("/station", methods={teapot.request.Method.GET})
@xsltea_site.with_template("view_stations.xml")
def view_stations(request:teapot.request.Request, page):
    stations = list(page)

    yield teapot.response.Response(
        None,
        last_modified=max(
            station.modified
            for station in stations))

    yield {
        "stations": stations,
        "view_stations": view_stations,
        "view_station": edit_station if request.auth else view_station,
        "delete_station": delete_station if request.auth else None,
        "page": page
    }, {}

@router.route("/station/{station_id:d}",
              methods={teapot.request.Method.GET})
@xsltea_site.with_variable_template()
def view_station(request: teapot.request.Request, station_id):
    station = request.dbsession.query(priyom.model.Station).get(station_id)

    yield ("station_view.xml" if station else "station_not_found.xml")

    yield teapot.response.Response(
        None,
        response_code=200 if station else 404,
        last_modified=station.modified if station else None)

    if station:
        yield {
            "station": station
        }, {}

    else:
        yield {
            "station_id": station_id
        }, {}

class StationForm(teapot.forms.Form):
    def __init__(self, from_station=None, **kwargs):
        super().__init__(**kwargs)
        if from_station is not None:
            self.id = from_station.id
            self.enigma_id = from_station.enigma_id
            self.priyom_id = from_station.priyom_id
            self.nickname = from_station.nickname or ""
            self.description = from_station.description or ""
            self.status = from_station.status or ""
            self.location = from_station.location or ""

    @teapot.forms.field
    def id(self, value):
        if not value:
            return None
        return int(value)

    @teapot.forms.field
    def enigma_id(self, value):
        if not value:
            return ""
        return str(value)

    @teapot.forms.field
    def priyom_id(self, value):
        if not value:
            return ""
        return str(value)

    @teapot.forms.field
    def nickname(self, value):
        return str(value)

    @teapot.forms.field
    def description(self, value):
        return str(value)

    @teapot.forms.field
    def status(self, value):
        return str(value)

    @teapot.forms.field
    def location(self, value):
        return str(value)

@require_capability("admin")
@router.route("/station/{station_id:d}/edit", methods={
    teapot.request.Method.GET})
@xsltea_site.with_template("station_form.xml")
def edit_station(station_id, request: teapot.request.Request):
    station = request.dbsession.query(priyom.model.Station).get(station_id)
    form = StationForm(from_station=station)
    yield teapot.response.Response(None)

    yield {
        "form": form
    }, {}

@require_capability("admin")
@router.route("/station/{station_id:d}/edit",
              methods={teapot.request.Method.POST})
@xsltea_site.with_template("station_form.xml")
def edit_station_POST(station_id, request: teapot.request.Request):
    dbsession = request.dbsession
    station = dbsession.query(priyom.model.Station).get(station_id)
    form = StationForm(post_data=request.post_data)

    if station_id != form.id:
        form.errors[StationForm.id] = "Invalid ID"

    if not form.errors:
        station.enigma_id = form.enigma_id
        station.priyom_id = form.priyom_id
        station.nickname = form.nickname
        station.description = form.description
        station.status = form.status
        station.location = form.location
        dbsession.commit()

        raise teapot.make_redirect_response(
            request,
            edit_station,
            station_id=form.id)

    else:
        yield teapot.response.Response(None)
        yield {
            "form": form
        }, {}

@require_capability("admin")
@router.route("/station/{station_id:d}/delete", methods={
    teapot.request.Method.GET})
@xsltea_site.with_template("station_delete.xml")
def delete_station(station_id, request: teapot.request.Request):
    yield teapot.response.Response(None)
    yield {}, {}
