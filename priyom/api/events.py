from datetime import datetime, timedelta

import sqlalchemy.exc
import sqlalchemy.orm.exc
from sqlalchemy import func
from sqlalchemy.orm import Session

import teapot
import teapot.forms

import priyom.model
import priyom.logic.fields

from .auth import *
from .dbview import *
from .event_forms import *
from .shared import *
from .utils import *

@require_capability(Capability.VIEW_EVENT)
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
            self.station_id = from_event.station_id
            self.start_time = from_event.start_time
            self.end_time = from_event.end_time
            self.event_class_id = from_event.event_class_id
            self.submitter_id = from_event.submitter_id
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

    def postvalidate(self, request):
        super().postvalidate(request)
        dbsession = request.dbsession
        if self.submitter_id is not None:
            submitter = dbsession.query(
                priyom.model.User
            ).get(self.submitter_id)
            if submitter is None:
                teapot.forms.ValidationError(
                    "Invalid user",
                    EventForm.submitter_id,
                    self).register()

        station = dbsession.query(
            priyom.model.Station
        ).get(self.station_id)
        if station is None:
            teapot.forms.ValidationError(
                "Invalid station",
                EventForm.station_id,
                self).register()

        if self.event_class_id is not None:
            event_class = dbsession.query(
                priyom.model.EventClass
            ).get(self.event_class_id)
            if event_class is None:
                teapot.forms.ValidationError(
                    "Invalid event class",
                    EventForm.event_class_id,
                    self).register()

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
@xsltea_site.with_template("event_form.xml")
def edit_event(event_id, request: teapot.request.Request):
    event = request.dbsession.query(priyom.model.Event).get(event_id)
    form = EventForm(from_event=event)

    yield from default_response(request, event, form)

@require_capability(Capability.EDIT_EVENT)
@router.route("/event/{event_id:d}/edit",
              methods={teapot.request.Method.POST})
@xsltea_site.with_template("event_form.xml")
def edit_event_POST(event_id, request: teapot.request.Request):
    dbsession = request.dbsession
    event = dbsession.query(priyom.model.Event).get(event_id)
    form = EventForm(request=request)

    revalidate = None
    action = form.find_action(request.post_data)
    if action is not None:
        target, action = action
    if action == "add_frequency":
        reference = dbsession.query(
            priyom.model.EventFrequency
        ).get(
            form.existing_broadcast_frequency_id
        )

        if reference is None:
            row = EventFrequencyRow()
            row.mode_id = next(iter(mode_picker_options(dbession)))
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
        event.station_id = form.station_id
        event.start_time = form.start_time
        event.end_time = form.end_time
        if request.auth.user.has_capability("moderator"):
            event.approved = form.approved
        if request.auth.user.has_capability("admin"):
            event.submitter_id = form.submitter_id
        event.event_class_id = form.event_class_id

        for existing in event.contents:
            dbsession.delete(existing)
        event.contents.clear()
        for contentrow in form.contents:
            fmt = contentrow.get_format(request)
            content = fmt.parse(contentrow.contents)
            content.attribution = contentrow.attribution
            content.alphabet_id = contentrow.alphabet_id
            for transcriptrow in contentrow.transcripts:
                transcribed = fmt.parse(transcriptrow.contents)
                transcribed.is_transcribed = True
                transcribed.attribution = transcriptrow.attribution
                transcribed.alphabet_id = transcriptrow.alphabet_id
                transcribed.parent_contents = content
                event.contents.append(transcribed)
            event.contents.append(content)
        dbsession.commit()

        raise teapot.make_redirect_response(
            request,
            edit_event,
            event_id=event_id)


    yield from default_response(request, event, form)

def get_event_viewer(request):
    """
    Return an event viewer call suitable for the logged-in user.

    Returns edit_event if the user has the appropriate capabilities and
    view_event otherwise.
    """

    if request.auth.has_capability(Capability.EDIT_EVENT):
        return edit_event
    else:
        return None
