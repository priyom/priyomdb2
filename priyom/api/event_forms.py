import re

import teapot.forms

import priyom.model

__all__ = [
    "EventFrequencyRow",
    "EventContentsRow",
    "EventTopLevelContentsRow"
]

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
