from datetime import datetime, timedelta
import re

import teapot.forms

import priyom.model

from .auth import *
from .event_forms import *
from .shared import *
from .utils import *

class LogPage1_Station(teapot.forms.Form):
    @teapot.forms.field
    def station_id(self, value):
        return int(value)

    @station_id.default
    def station_id(self):
        return 0

    @teapot.forms.field
    def timestamp(self, value):
        return parse_datetime(value)

    @timestamp.default
    def timestamp(self):
        return datetime.utcnow().replace(microsecond=0, second=0)

    def postvalidate(self, request):
        super().postvalidate(request)
        if self.station_id != 0:
            dbsession = request.dbsession
            if not dbsession.query(priyom.model.Station).get(self.station_id):
                teapot.forms.ValidationError(
                    "Non-existant station selected",
                    LogPage1_Station.station_id,
                    self).register()

class LogPage2_Broadcast(teapot.forms.Form):
    @teapot.forms.field
    def broadcast_source(self, value):
        if value == "new":
            return "new"
        else:
            return "existing"

    @broadcast_source.default
    def broadcast_source(self):
        return "new"

    @teapot.forms.field
    def broadcast_id(self, value):
        return int(value)

    @broadcast_id.default
    def broadcast_id(self):
        return 0

    @teapot.forms.field
    def existing_broadcast_frequency_id(self, value):
        return int(value)

    @existing_broadcast_frequency_id.default
    def existing_broadcast_frequency_id(self):
        return 0

    frequencies = teapot.forms.rows(EventFrequencyRow)

    def postvalidate(self, request):
        super().postvalidate(request)
        dbsession = request.dbsession
        if self.broadcast_source == "existing":
            if not dbsession.query(priyom.model.Event).get(self.broadcast_id):
                teapot.forms.ValidationError("Not a valid broadcast",
                                             LogPage2_Broadcast.broadcast_id,
                                             self).register()
        else:
            if not self.frequencies:
                teapot.forms.ValidationError("At least one frequency is required",
                                             LogPage2_Broadcast.frequencies,
                                             self).register()

class LogPage3_Contents(teapot.forms.Form):
    contents = teapot.forms.rows(EventTopLevelContentsRow)

@require_capability(Capability.LOG)
@router.route("/action/log", methods={teapot.request.Method.GET})
@xsltea_site.with_template("log1.xml")
def log(request: teapot.request.Request):
    dbsession = request.dbsession

    contents = LogPage3_Contents()
    contents.contents.append(
        EventTopLevelContentsRow())

    pages = [
        LogPage1_Station(),
        LogPage2_Broadcast(),
        contents
    ]

    yield teapot.response.Response(None)
    yield {
        "pages": pages,
        "pageidx": 0,
        "stations": dbsession.query(priyom.model.Station
                                ).order_by(priyom.model.Station.enigma_id.asc())
    }, {}

@require_capability(Capability.LOG)
@router.route("/action/log", methods={teapot.request.Method.POST})
@xsltea_site.with_variable_template()
def log_POST(request: teapot.request.Request):
    dbsession = request.dbsession

    pages = [
        LogPage1_Station(request=request),
        LogPage2_Broadcast(request=request),
        LogPage3_Contents(request=request)
    ]

    try:
        currpage = int(request.post_data.pop("currpage").pop())
        if currpage < 0 or currpage >= len(pages):
            raise ValueError()
    except (KeyError, ValueError):
        currpage = 0

    if "forward" in request.post_data:
        currpage = min(currpage+1, len(pages)-1)
    elif "backward" in request.post_data:
        currpage = max(currpage-1, 0)

    for page_index in range(currpage+1):
        page = pages[page_index]
        if page.errors:
            currpage = page_index
            break

    template = "log{}.xml".format(currpage+1)

    yield template

    template_args = {
        "pages": pages,
        "pageidx": currpage
    }

    page = pages[currpage]
    if currpage == 0:
        template_args["stations"] = station_id_picker_options(
            dbsession)
    elif currpage == 1:
        interval = timedelta(seconds=600)
        start_time_min = pages[0].timestamp - interval
        start_time_max = pages[0].timestamp + interval

        template_args["events"] = dbsession.query(
            priyom.model.Event
        ).filter(
            priyom.model.Event.station_id == pages[0].station_id,
            priyom.model.Event.event_class_id == None,
            priyom.model.Event.start_time >= start_time_min,
            priyom.model.Event.start_time <= start_time_max
        ).order_by(
            priyom.model.Event.start_time.asc())

        template_args["modes"] = list(mode_picker_options(dbsession))

        template_args["frequencies"] = frequency_picker_options(
            dbsession, for_event=pages[0])

        action = page.find_action(request.post_data)
        if action is not None:
            target, action = action
        if action == "add_frequency":
            reference_id = page.existing_broadcast_frequency_id
            event_frequency = dbsession.query(
                priyom.model.EventFrequency).get(reference_id)
            if event_frequency is not None:
                row = EventFrequencyRow(reference=event_frequency)
            else:
                row = EventFrequencyRow()
                row.mode_id = template_args["modes"][0].id
                row.frequency = "0"
            page.frequencies.append(row)
            # re-run post-validation
            try:
                del page.errors[LogPage2_Broadcast.frequencies]
            except KeyError:
                pass
            page.postvalidate(request)
        elif action == "delete":
            del target.parent[target.index]
            # re-run post-validation
            try:
                del page.errors[LogPage2_Broadcast.frequencies]
            except KeyError:
                pass
            page.postvalidate(request)
    elif currpage == 2:
        template_args["formats"] = list(format_picker_options(dbsession))
        template_args["alphabets"] = list(alphabet_picker_options(dbsession))

        action = page.find_action(request.post_data)
        if action is not None:
            target, action = action
        if action == "add_contents":
            row = EventTopLevelContentsRow()
            page.contents.append(row)
        elif action == "add_transcript":
            row = EventContentsRow()
            row.contents = target.contents
            target.transcripts.append(row)
        elif action == "delete":
            del target.parent[target.index]
        elif action == "save" and not any(page.errors for page in pages):
            if pages[1].broadcast_source == "new":
                event = priyom.model.Event()
                event.station_id = pages[0].station_id
                event.start_time = pages[0].timestamp
                event.end_time = pages[0].timestamp
                event.approved = any(
                    request.auth.user.has_capability(Capability.LOG_UNMODERATED))
                event.submitter = request.auth.user
                for row in pages[1].frequencies:
                    frequency = priyom.model.EventFrequency()
                    frequency.frequency = row.frequency
                    frequency.mode_id = row.mode_id
                    event.frequencies.append(frequency)
            else:
                event = dbsession.query(priyom.model.Broadcast).get(
                    pages[1].broadcast_id)

            for contentrow in pages[2].contents:
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

            dbsession.add(event)
            dbsession.commit()
            from . import dash
            raise teapot.make_redirect_response(
                request,
                dash.dash)

    yield teapot.response.Response(None)
    yield template_args, {}
