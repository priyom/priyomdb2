from datetime import datetime, timedelta

import sqlalchemy.exc
import sqlalchemy.orm.exc
from sqlalchemy import func
from sqlalchemy.orm import Session

import teapot
import teapot.forms
import teapot.sqlalchemy

import priyom.model
import priyom.logic.fields

from .auth import *
from .event_forms import *
from .shared import *
from .utils import *

events_view_form = teapot.sqlalchemy.dbview.make_form(
    priyom.model.Event,
    [
        ("id", priyom.model.Event.id, None),
        ("modified", priyom.model.Event.modified, None),
        ("station_id", priyom.model.Station.id, None),
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
    supplemental_objects=[priyom.model.Station,
                          ("outerjoin", priyom.model.User)],
    objects="primary")

@require_capability(Capability.VIEW_EVENT)
@teapot.sqlalchemy.dbview.dbview(events_view_form)
@router.route("/event",
              methods={teapot.request.Method.GET})
@xsltea_site.with_template("view_events.xml")
def view_events(request: teapot.request.Request, view):
    from .stations import get_station_viewer

    yield teapot.response.Response(None)
    yield {
        "view_events": view_events,
        "view_station": get_station_viewer(request),
        "view": view,
        "edit_event": get_event_viewer(request)
    }, {}


class EventForm(teapot.forms.Form):
    def __init__(self, from_event=None, **kwargs):
        super().__init__(**kwargs)
        if from_event is not None:
            self.station = from_event.station
            self.start_time = from_event.start_time
            self.end_time = from_event.end_time
            self.event_class = from_event.event_class
            self.submitter = from_event.submitter
            self.approved = from_event.approved
            for freq in from_event.frequencies:
                self.frequencies.append(EventFrequencyRow(
                    reference=freq))
            for content in from_event.contents:
                if content.parent_contents is not None:
                    continue
                self.contents.append(EventTopLevelContentsRow(
                    from_contents=content))

    station = priyom.logic.fields.ObjectRefField(
        priyom.model.Station,
        allow_none=False)

    start_time = teapot.html.DateTimeField(
        teapot.html.DateTimeMode.Full & teapot.html.DateTimeMode.Minute,
        "datetime")

    end_time = teapot.html.DateTimeField(
        teapot.html.DateTimeMode.Full & teapot.html.DateTimeMode.Minute,
        "datetime",
        allow_none=True)

    event_class = priyom.logic.fields.ObjectRefField(
        priyom.model.EventClass,
        allow_none=True)

    submitter = priyom.logic.fields.ObjectRefField(
        priyom.model.User,
        allow_none=True)

    approved = teapot.html.CheckboxField(default=True)

    existing_event_frequency = priyom.logic.fields.ObjectRefField(
        priyom.model.EventFrequency,
        allow_none=True)

    frequencies = teapot.forms.Rows(EventFrequencyRow)
    contents = teapot.forms.Rows(EventTopLevelContentsRow)

def default_response(request, event, form):
    yield teapot.response.Response(None)
    yield {
        "form": form,
        "event": event,
        "stations": station_id_picker_options(request.dbsession),
        "event_classes": request.dbsession.query(priyom.model.EventClass),
        "users": request.dbsession.query(priyom.model.User),
        "modes": list(mode_picker_options(request.dbsession)),
        "alphabets": list(alphabet_picker_options(request.dbsession)),
        "formats": list(format_picker_options(request.dbsession)),
        "existing_frequencies": frequency_picker_options(request.dbsession,
                                                         for_event=event)
    }, {}

@require_capability(Capability.EDIT_EVENT)
@router.route("/event/{event_id:d}/edit",
              methods={teapot.request.Method.GET})
@xsltea_site.with_variable_template()
def edit_event(event_id, request: teapot.request.Request):
    event = request.dbsession.query(priyom.model.Event).get(event_id)

    if event is None:
        yield "event_not_found.xml"
        yield teapot.response.Response(None, response_code=404)
        yield {"event_id": event_id}, {}
    else:
        yield "event_form.xml"
        form = EventForm(from_event=event)
        yield from default_response(request, event, form)

@require_capability(Capability.EDIT_EVENT)
@router.route("/event/{event_id:d}/edit",
              methods={teapot.request.Method.POST})
@xsltea_site.with_template("event_form.xml")
def edit_event_POST(event_id, request: teapot.request.Request):
    dbsession = request.dbsession
    event = dbsession.query(priyom.model.Event).get(event_id)
    if event is None:
        raise teapot.make_redirect_response(
            request,
            edit_event,
            event_id=event_id)

    form = EventForm(request=request)

    revalidate = None
    action = form.find_action(request.post_data)
    if action is not None:
        target, action = action
    if action == "add_frequency":
        reference = dbsession.query(
            priyom.model.EventFrequency
        ).get(
            form.existing_event_frequency
        )

        if reference is None:
            row = EventFrequencyRow()
            row.mode = next(iter(mode_picker_options(dbession)))
            row.frequency = "0"
        else:
            row = EventFrequencyRow(reference=reference)

        form.frequencies.append(row)

        revalidate = EventForm.frequencies
    elif action == "delete":
        del target.parent[target.index]
        revalidate = target.parent
    elif action == "add_transcript":
        row = EventContentsRow()
        row.contents = target.contents
        target.transcripts.append(row)
    elif action == "validate":
        pass

    if revalidate is not None:
        try:
            del form.errors[revalidate]
        except KeyError:
            pass
        revalidate.postvalidate(form, request)

    if not form.errors and action == "save":
        event.station = form.station
        event.start_time = form.start_time
        event.end_time = form.end_time
        if request.auth.has_capability(Capability.REVIEW_LOG):
            event.approved = form.approved
        if request.auth.has_capability(Capability.REASSIGN_EVENT):
            event.submitter = form.submitter
        event.event_class = form.event_class

        for existing in event.contents:
            dbsession.delete(existing)
        event.contents.clear()
        event.contents.extend(event_rows_to_contents(
            request,
            form.contents))
        dbsession.commit()

        raise teapot.make_redirect_response(
            request,
            edit_event,
            event_id=event_id)


    yield from default_response(request, event, form)

class ApproveForm(teapot.forms.Form):
    event = priyom.logic.fields.ObjectRefField(
        priyom.model.Event,
        allow_none=False)

def filter_unapproved(request, query):
    return query.filter(priyom.model.Event.approved == False)

@require_capability(Capability.REVIEW_LOG)
@teapot.sqlalchemy.dbview.dbview(teapot.sqlalchemy.dbview.make_form(
    priyom.model.Event,
    [
        ("id", priyom.model.Event.id, None),
        ("created", priyom.model.Event.created, None),
        ("modified", priyom.model.Event.modified, None),
        ("station",
         priyom.model.Station.enigma_id + ' / ' + priyom.model.Station.priyom_id,
         str),
        ("submitter_id",
         priyom.model.User.id, None),
        ("submitter",
         priyom.model.User.loginname, None)
    ],
    default_orderfield="created",
    default_orderdir="asc",
    supplemental_objects=[priyom.model.Station, priyom.model.User],
    custom_filter=filter_unapproved,
    objects="primary"))
@router.route("/review",
              methods={teapot.request.Method.GET})
@xsltea_site.with_template("review.xml")
def review(request: teapot.request.Request, view):
    from .stations import get_station_viewer

    yield teapot.response.Response(None)
    yield {
        "view_station": get_station_viewer(request),
        "view": view,
        "view_event": get_event_viewer(request),
        "review": review,
        "approve_form": ApproveForm(),
    }, {}

@require_capability(Capability.REVIEW_LOG)
@router.route("/review",
              methods={teapot.request.Method.POST})
@xsltea_site.with_template("review.xml")
def review_POST(request: teapot.request.Request):
    dbsession = request.dbsession
    form = ApproveForm(request=request)

    if not form.errors and not form.event.approved:
        _, action = form.find_action(request.post_data)
        if action == "approve":
            form.event.approved = True
            dbsession.commit()
        elif action == "delete":
            dbsession.delete(form.event)
            dbsession.commit()

    raise teapot.make_redirect_response(
        request,
        review,
        view=view)

@require_capability(Capability.VIEW_EVENT)
@router.route("/event/{event_id:d}",
              methods={teapot.request.Method.GET})
@xsltea_site.with_variable_template()
def view_event(event_id, request: teapot.request.Request):
    event = request.dbsession.query(priyom.model.Event).get(event_id)

    if event is None:
        yield "event_not_found.xml"
        yield teapot.response.Response(None, response_code=404)
        yield {"event_id": event_id}, {}
    else:
        yield "event_view.xml"
        yield teapot.response.Response(None)
        yield {"event": event}, {}


def get_event_viewer(request):
    """
    Return an event viewer call suitable for the logged-in user.

    Returns edit_event if the user has the appropriate capabilities and
    view_event otherwise.
    """

    if request.auth.has_capability(Capability.EDIT_EVENT):
        return edit_event
    else:
        return view_event
