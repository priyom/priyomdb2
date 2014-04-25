import logging
import re

import teapot.forms

import priyom.model

__all__ = [
    "alphabet_picker_options",
    "format_picker_options",
    "frequency_picker_options",
    "mode_picker_options",
    "station_id_picker_options",
    "EventFrequencyRow",
    "EventContentsRow",
    "EventTopLevelContentsRow",
]

logger = logging.getLogger(__name__)

def alphabet_picker_options(dbsession):
    return dbsession.query(
        priyom.model.Alphabet
    ).order_by(
        priyom.model.Alphabet.display_name.asc()
    )

def format_picker_options(dbsession):
    return dbsession.query(
        priyom.model.TransmissionFormat
    ).order_by(
        priyom.model.TransmissionFormat.display_name.asc()
    )

def frequency_picker_options(dbsession, for_event=None):
    query = dbsession.query(
        priyom.model.EventFrequency
    ).join(
        priyom.model.Event
    ).group_by(
        priyom.model.EventFrequency.frequency,
        priyom.model.EventFrequency.mode_id
    )

    if for_event is not None:
        query = query.filter(
            priyom.model.Event.station_id == for_event.station_id
        )
    return query

def mode_picker_options(dbsession):
    return dbsession.query(
        priyom.model.Mode
    ).order_by(
        priyom.model.Mode.display_name.asc())

def station_id_picker_options(dbsession):
    return dbsession.query(
        priyom.model.Station
    ).order_by(
        priyom.model.Station.enigma_id.asc()
    )

class EventFrequencyRow(teapot.forms.Row):
    FREQUENCY_RE = re.compile(
        r"^([0-9]+(\.[0-9]*)?|[0-9]*\.[0-9]+)\s*(([a-z]?)Hz)?$",
        re.I)

    def __init__(self, *args, reference=None, **kwargs):
        super().__init__(*args, **kwargs)
        if reference is not None:
            self.fields[EventFrequencyRow.frequency.name] = reference.frequency
            self.mode_id = reference.mode_id

    @teapot.forms.field
    def frequency(self, value):
        try:
            value, _, unit, prefix = self.FREQUENCY_RE.match(value).groups()
        except AttributeError:
            # NoneType has no attribute `groups'
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
    def mode_id(self, value):
        return int(value)

    @mode_id.default
    def mode_id(self):
        return 0

    def postvalidate(self, request):
        super().postvalidate(request)
        dbsession = request.dbsession
        if not dbsession.query(priyom.model.Mode).get(self.mode_id):
            teapot.forms.ValidationError("Not a valid mode",
                                         EventFrequencyRow.mode_id,
                                         self).register()

class EventContentsRow(teapot.forms.Row):
    def __init__(self, from_contents=None, **kwargs):
        super().__init__(**kwargs)
        if from_contents is not None:
            self.alphabet_id = from_contents.alphabet_id
            # this will crash for raw contents -- which are not fully supported
            # yet!
            self.contents = from_contents.unparse() # AttributeError here? see above
            self.attribution = from_contents.attribution

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

    def get_format(self, request):
        return self.parent.instance.get_format(request)

    def postvalidate(self, request):
        super().postvalidate(request)
        dbsession = request.dbsession
        fmt = self.get_format(request)
        if fmt is not None:
            try:
                fmt.root_node.parse(self.contents)
            except ValueError:
                teapot.forms.ValidationError("Message does not match format",
                                             EventContentsRow.contents,
                                             self).register()

        alphabet = dbsession.query(priyom.model.Alphabet).get(self.alphabet_id)
        if not alphabet:
            teapot.forms.ValidationError("Not a valid alphabet",
                                         EventContentsRow.alphabet_id,
                                         self).register()

class EventTopLevelContentsRow(EventContentsRow):
    def __init__(self, from_contents=None, with_children=True, **kwargs):
        super().__init__(from_contents=from_contents, **kwargs)
        if from_contents is not None:
            self.format_id = from_contents.format_id
            if with_children:
                for child in from_contents.children:
                    if not child.is_transcribed:
                        logger.warn("unhandled child in contents row: %s",
                                    child)
                        continue

                    self.transcripts.append(EventContentsRow(
                        from_contents=child))

    @teapot.forms.field
    def format_id(self, value):
        if value == 'None':
            return None
        return int(value)

    @format_id.default
    def format_id(self):
        return 0

    def get_format(self, request):
        dbsession = request.dbsession
        fmt = dbsession.query(
            priyom.model.TransmissionFormat
        ).get(self.format_id)
        return fmt

    def postvalidate(self, request):
        fmt = self.get_format(request)
        if fmt is None:
            teapot.forms.ValidationError("Not a valid transmission format",
                                         EventTopLevelContentsRow.format_id,
                                         self).register()

        super().postvalidate(request)

    transcripts = teapot.forms.rows(EventContentsRow)
