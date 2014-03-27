from datetime import datetime, timedelta
import re

import teapot.forms

import priyom.model

from .auth import *
from .shared import *

datetime_formats = [
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%MZ",
    "%Y-%m-%dT%H:%M",
]

def parse_isodate_full(s):
    if s.endswith("Z"):
        s = s[:-1]
    date, sep, milliseconds = s.rpartition(".")
    if sep is not None:
        fracseconds = float(sep+milliseconds)
    date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
    return date.replace(
        microsecond=int(fracseconds*1000000))

def parse_datetime(s):
    # format with milliseconds
    try:
        return parse_isodate_full(s)
    except ValueError:
        pass

    for fmt in datetime_formats:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    else:
        raise ValueError("Not a valid UTC timestamp".format(s))

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
        return datetime.utcnow()

    def postvalidate(self, request):
        super().postvalidate(request)
        if self.station_id != 0:
            dbsession = request.dbsession
            if not dbsession.query(priyom.model.Station).get(self.station_id):
                teapot.forms.ValidationError(
                    "Non-existant station selected",
                    LogPage1_Station.station_id,
                    self).register()

class BroadcastFrequencyRow(teapot.forms.Row):
    FREQUENCY_RE = re.compile(
        r"^([0-9]+(\.[0-9]*)?|[0-9]*\.[0-9]+)\s*(([a-z]?)Hz)?$",
        re.I)

    def __init__(self, *args, reference=None, **kwargs):
        super().__init__(*args, **kwargs)
        if reference is not None:
            self.fields[BroadcastFrequencyRow.frequency.name] = reference.frequency
            self.modulation_id = reference.modulation_id

    @teapot.forms.field
    def frequency(self, value):
        try:
            value, _, prefix, unit = self.FREQUENCY_RE.match(value).groups()
        except AttributeError:
            # NoneType has no attribute groups
            raise ValueError("Not a valid frequency. Specify like this: "
                             "10.4 MHz or 1000 Hz or 123.4 kHz")

        try:
            factor = {
                None: 1,
                "k": 1000,
                "m": 1000000,
                "g": 1000000000,
                "t": 1000000000000
            }[prefix.lower() if prefix else None]
        except KeyError:
            raise ValueError("Unknown unit prefix")

        return round(float(value) * factor)

    @frequency.default
    def frequency(self):
        return 0

    @teapot.forms.field
    def modulation_id(self, value):
        return int(value)

    @modulation_id.default
    def modulation_id(self):
        return 0

    def postvalidate(self, request):
        super().postvalidate(request)
        dbsession = request.dbsession
        if not dbsession.query(priyom.model.Modulation).get(self.modulation_id):
            teapot.forms.ValidationError("Not a valid modulation",
                                         BroadcastFrequencyRow.modulation_id,
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

    frequencies = teapot.forms.rows(BroadcastFrequencyRow)

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


class ContentsRow(teapot.forms.Row):
    @teapot.forms.field
    def alphabet_id(self, value):
        return int(value)

    @alphabet_id.default
    def alphabet_id(self):
        return 0

    @teapot.forms.field
    def contents(self, value):
        return value

    @contents.default
    def contents(self):
        return ""

    @teapot.forms.field
    def attribution(self, value):
        return value

    @attribution.default
    def attribution(self):
        return ""

    def postvalidate(self, request):
        dbsession = request.dbsession
        fmt = dbsession.query(
            priyom.model.TransmissionFormat
        ).get(self.format_id)
        if fmt is None:
            teapot.forms.ValidationError("Not a valid transmission format",
                                         ContentsRow.format_id,
                                         self).register()
            return

        try:
            fmt.root_node.parse(self.contents)
        except ValueError:
            teapot.forms.ValidationError("Message does not match format",
                                         ContentsRow.contents,
                                         self).register()

        if not dbsession.query(priyom.model.Alphabet).get(self.alphabet_id):
            teapot.forms.ValidationError("Not a valid alphabet",
                                         ContentsRow.alphabet_id,
                                         self).register()

class TopLevelContentsRow(ContentsRow):
    @teapot.forms.field
    def format_id(self, value):
        return int(value)

    @format_id.default
    def format_id(self):
        return 0

    transcripts = teapot.forms.rows(ContentsRow)

class LogPage3_Contents(teapot.forms.Form):
    contents = teapot.forms.rows(TopLevelContentsRow)

@require_capability("log", "admin", "log_moderated", "moderator")
@router.route("/action/log", methods={teapot.request.Method.GET})
@xsltea_site.with_template("log1.xml")
def log(request: teapot.request.Request):
    dbsession = request.dbsession

    pages = [
        LogPage1_Station(),
        LogPage2_Broadcast(),
        LogPage3_Contents()
    ]

    yield teapot.response.Response(None)
    yield {
        "pages": pages,
        "pageidx": 0,
        "stations": dbsession.query(priyom.model.Station
                                ).order_by(priyom.model.Station.enigma_id.asc())
    }, {}

@require_capability("log", "admin", "log_moderated", "moderator")
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

    template = "log{}.xml".format(currpage+1)

    yield template
    yield teapot.response.Response(None)

    template_args = {
        "pages": pages,
        "pageidx": currpage
    }

    page = pages[currpage]
    if currpage == 0:
        template_args["stations"] = dbsession.query(
            priyom.model.Station
        ).order_by(
            priyom.model.Station.enigma_id.asc()
        )
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

        template_args["modulations"] = list(dbsession.query(
            priyom.model.Modulation
        ).order_by(
            priyom.model.Modulation.display_name.asc()))

        template_args["frequencies"] = dbsession.query(
            priyom.model.EventFrequency
        ).join(
            priyom.model.Event
        ).group_by(
            priyom.model.EventFrequency.frequency,
            priyom.model.EventFrequency.modulation_id
        ).filter(
            priyom.model.Event.station_id == pages[0].station_id
        )

        action = page.find_action(request.post_data)
        if action is not None:
            target, action = action
        if action == "add":
            reference_id = page.existing_broadcast_frequency_id
            event_frequency = dbsession.query(
                priyom.model.EventFrequency).get(reference_id)
            if event_frequency is not None:
                row = BroadcastFrequencyRow(reference=event_frequency)
            else:
                row = BroadcastFrequencyRow()
                row.modulation_id = template_args["modulations"][0].id
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
        template_args["formats"] = list(dbsession.query(
            priyom.model.TransmissionFormat
        ).order_by(
            priyom.model.TransmissionFormat.display_name.asc()
        ))

        template_args["alphabets"] = list(dbsession.query(
            priyom.model.Alphabet
        ).order_by(
            priyom.model.Alphabet.display_name.asc()
        ))

        action = page.find_action(request.post_data)
        if action is not None:
            target, action = action
        if action == "add":
            row = TopLevelContentsRow()
            page.contents.append(row)
        elif action == "add_transcript":
            row = ContentsRow()
            row.contents = target.contents
            target.transcripts.append(row)
        elif action == "delete_transcript":
            del target.parent[target.index]
        elif action == "delete":
            del target.parent[target.index]

    yield template_args, {}
