import logging

import teapot.forms

import priyom.model

from . import fields

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
    def __init__(self, *args, reference=None, **kwargs):
        super().__init__(*args, **kwargs)
        if reference is not None:
            self.frequency = reference.frequency
            self.mode_id = reference.mode_id

    frequency = fields.FrequencyField()
    mode = fields.ObjectRefField(
        priyom.model.Mode,
        allow_none=False)

class EventContentsRow(teapot.forms.Row):
    def __init__(self, from_contents=None, **kwargs):
        super().__init__(**kwargs)
        if from_contents is not None:
            self.alphabet_id = from_contents.alphabet_id
            # this will crash for raw contents -- which are not fully supported
            # yet!
            self.contents = from_contents.unparse() # AttributeError here? see above
            self.attribution = from_contents.attribution

    alphabet = fields.ObjectRefField(priyom.model.Alphabet)
    attribution = teapot.forms.TextField()
    contents = teapot.forms.TextField()

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

    format = fields.ObjectRefField(priyom.model.TransmissionFormat)

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

    transcripts = teapot.forms.Rows(EventContentsRow)
