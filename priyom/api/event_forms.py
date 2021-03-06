import logging

import teapot.forms

import priyom.model
import priyom.logic.fields

__all__ = [
    "alphabet_picker_options",
    "format_picker_options",
    "frequency_picker_options",
    "mode_picker_options",
    "station_id_picker_options",
    "EventFrequencyRow",
    "EventContentsRow",
    "EventTopLevelContentsRow",
    "event_rows_to_contents",
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
        priyom.model.Format
    ).order_by(
        priyom.model.Format.display_name.asc()
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
            priyom.model.Event.station_id == for_event.station.id
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
            self.mode = reference.mode

    frequency = priyom.logic.fields.FrequencyField()
    mode = priyom.logic.fields.ObjectRefField(
        priyom.model.Mode,
        allow_none=False,
        provide_options=True)

class EventContentsRow(teapot.forms.Row):
    def __init__(self, from_contents=None, **kwargs):
        super().__init__(**kwargs)
        if from_contents is not None:
            self.alphabet = from_contents.alphabet
            self.contents = str(from_contents)
            self.attribution = from_contents.attribution

    alphabet = priyom.logic.fields.ObjectRefField(priyom.model.Alphabet)
    attribution = teapot.forms.TextField()
    contents = teapot.forms.TextField()

    def get_format(self, request):
        return self.parent.instance.get_format(request)

    def postvalidate(self, request):
        super().postvalidate(request)
        dbsession = request.dbsession
        type_, fmt = self.get_format(request)
        if fmt is not None:
            try:
                fmt.root_node.parse(self.contents)
            except ValueError:
                teapot.forms.ValidationError("Message does not match format",
                                             EventContentsRow.contents,
                                             self).register()
        else:
            try:
                type_.parse(self.contents)
            except ValueError:
                teapot.forms.ValidationError("Message does not match format",
                                             EventContentsRow.contents,
                                             self).register()

class EventTopLevelContentsRow(EventContentsRow):
    def __init__(self, from_contents=None, with_children=True, **kwargs):
        super().__init__(from_contents=from_contents, **kwargs)
        if from_contents is not None:
            if hasattr(from_contents, "format"):
                self.format = type(from_contents), from_contents.format
            else:
                self.format = type(from_contents), None
            if with_children:
                for child in from_contents.children:
                    if not child.is_transcribed:
                        logger.warn("unhandled child in contents row: %s",
                                    child)
                        continue

                    self.transcripts.append(EventContentsRow(
                        from_contents=child))

    format = priyom.logic.fields.TransmissionFormatField()

    def get_format(self, request):
        return self.format

    transcripts = teapot.forms.Rows(EventContentsRow)

def single_row_to_contents(request, row):
    type_, fmt = row.get_format(request)
    if fmt is not None:
        content = type_("text/plain", fmt)
    else:
        content = type_(type_.parse(row.contents))
    content.attribution = row.attribution
    content.alphabet = row.alphabet
    return content

def event_rows_to_contents(request, rows):
    for contentrow in rows:
        content = single_row_to_contents(request, contentrow)
        for transcriptrow in contentrow.transcripts:
            transcribed = single_row_to_contents(request, transcriptrow)
            transcribed.parent_contents = content
            yield transcribed
        yield content
