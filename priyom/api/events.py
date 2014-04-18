import sqlalchemy.exc
import sqlalchemy.orm.exc
from sqlalchemy import func
from sqlalchemy.orm import Session

import teapot

import priyom.model

from .auth import *
from .dbview import *
from .shared import *

@dbview(priyom.model.Event,
        [
            ("id", priyom.model.Event.id, None),
            ("modified", priyom.model.Event.modified, None),
            ("station_id", priyom.model.Station.id, None),
            ("station_obj", priyom.model.Station, None),
            ("station",
             priyom.model.Station.enigma_id + ' / ' + priyom.model.Station.priyom_id,
             str),
            ("submitter_id",
             priyom.model.User.id, None),
            ("submitter",
             priyom.model.User.loginname, None),
            ("start_time", priyom.model.Event.start_time, None)
        ],
        default_orderfield="modified",
        default_orderdir="desc",
        supplemental_objects=[priyom.model.Station],
        provide_primary_object=True)
@router.route("/event",
              methods={teapot.request.Method.GET})
@xsltea_site.with_template("view_events.xml")
def view_events(request: teapot.request.Request, view):
    from .stations import view_station, edit_station

    yield teapot.response.Response(None)
    yield {
        "view_events": view_events,
        "view_station": (edit_station
                         if (request.auth and
                             request.auth.user.has_capability("admin"))
                         else view_station),
        "view": view
    }, {}
