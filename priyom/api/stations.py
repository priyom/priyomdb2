import sqlalchemy.exc
import sqlalchemy.orm.exc
from sqlalchemy import func
from sqlalchemy.orm import Session

import teapot

import priyom.model

from .auth import *
from .dbview import *
from .shared import *

def get_recent_events(station):
    if station is not None:
        dbsession = Session.object_session(station)
        recent_events = dbsession.query(
            priyom.model.Event
        ).filter(
            priyom.model.Event.station_id == station.id
        )
    else:
        recent_events = None

    return recent_events

def get_event_view(station):
    if station is None:
        return None
    from .events import view_events
    dbsession = Session.object_session(station)
    view = view_events.dbview.new_view(
        dbsession,
        station_id=station.id)
    return view

@dbview(priyom.model.Station,
        [
            ("id", priyom.model.Station.id, None),
            ("modified", priyom.model.Station.modified, None),
            ("enigma_id", priyom.model.Station.enigma_id, None),
            ("priyom_id", priyom.model.Station.priyom_id, None),
            ("nickname", priyom.model.Station.nickname, None),
            ("events",
             subquery(
                 priyom.model.Event,
                 func.count('*').label("events")
             ).with_labels().group_by(
                 priyom.model.Event.station_id
             ),
             int)
        ],
        itemsperpage=25,
        default_orderfield="enigma_id")
@router.route("/station", methods={teapot.request.Method.GET})
@xsltea_site.with_template("view_stations.xml")
def view_stations(request: teapot.request.Request, view):
    yield teapot.response.Response(None)

    yield {
        "view_stations": view_stations,
        "view_station": edit_station if request.auth else view_station,
        "delete_station": delete_station if request.auth else None,
        "view": view
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
        from .events import view_events
        yield {
            "station": station,
            "view_events": view_events,
            "event_view": get_event_view(station),
            "recent_events": get_recent_events(station)
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

    def postvalidate(self, request):
        super().postvalidate(request)
        dbsession = request.dbsession

        try:
            duplicate = dbsession.query(
                priyom.model.Station
            ).filter(
                priyom.model.Station.enigma_id == self.enigma_id,
                priyom.model.Station.priyom_id == self.priyom_id
            ).one()
        except sqlalchemy.orm.exc.NoResultFound:
            pass
        else:
            if duplicate.id != self.id:
                teapot.forms.ValidationError(
                    "This combination of enigma ID and priyom ID already "
                    "exists.",
                    None,
                    self).register()

@require_capability("admin")
@router.route("/station/{station_id:d}/edit", methods={
    teapot.request.Method.GET})
@xsltea_site.with_template("station_form.xml")
def edit_station(station_id, request: teapot.request.Request):
    station = request.dbsession.query(priyom.model.Station).get(station_id)
    form = StationForm(from_station=station)
    yield teapot.response.Response(None)

    from .events import view_events
    yield {
        "form": form,
        "station_id": station_id,
        "view_events": view_events,
        "recent_events": get_recent_events(station),
        "event_view": get_event_view(station),
    }, {}

@require_capability("admin")
@router.route("/station/{station_id:d}/edit",
              methods={teapot.request.Method.POST})
@xsltea_site.with_template("station_form.xml")
def edit_station_POST(station_id, request: teapot.request.Request):
    dbsession = request.dbsession
    station = dbsession.query(priyom.model.Station).get(station_id)
    form = StationForm(post_data=request.post_data)
    form.id = station_id
    form.postvalidate(request)

    if not form.errors:
        try:
            if station is None:
                station = priyom.model.Station(
                    form.enigma_id,
                    form.priyom_id)
            else:
                station.enigma_id = form.enigma_id
                station.priyom_id = form.priyom_id
            station.nickname = form.nickname
            station.description = form.description
            station.status = form.status
            station.location = form.location
            dbsession.add(station)
            dbsession.commit()
        except sqlalchemy.orm.exc.IntegrityError as err:
            dbsession.rollback()
            teapot.forms.ValidationError(
                "An unspecified integrity error occured: {}".format(
                    err),
                None,
                form).register()
        else:
            raise teapot.make_redirect_response(
                request,
                edit_station,
                station_id=station.id)

    yield teapot.response.Response(None)

    from .events import view_events
    yield {
        "form": form,
        "station_id": station_id,
        "view_events": view_events,
        "recent_events": get_recent_events(station),
        "event_view": get_event_view(station)
    }, {}

@require_capability("admin")
@router.route("/station/{station_id:d}/delete",
              methods={teapot.request.Method.GET})
@xsltea_site.with_template("station_delete.xml")
def delete_station(station_id, request: teapot.request.Request):
    yield teapot.response.Response(None)
    yield {}, {}
