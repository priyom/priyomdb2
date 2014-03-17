import collections

import teapot
import teapot.forms
import teapot.response
import teapot.request

import priyom.model
import priyom.logic

import sqlalchemy.exc

from .shared import *
from .auth import *
from .pagination import *

def mdzhb_format():
    TF, TFN = priyom.model.TransmissionFormat, priyom.model.TransmissionFormatNode
    call = TFN("[0-9]{2}\s+[0-9]{3}", key="call", comment="“Callsign”")
    callwrap = TFN(
        call,
        duplicity="+",
        separator=" ",
        key="callwrap",
        saved=False,
        comment="Group callsigns separated with space"
    )
    codeword = TFN("\w+",
                   key="codeword",
                   comment="Single word")
    numbers = TFN("([0-9]{2} ){3}[0-9]{2}",
                  key="numbers",
                  comment="Four two-digit numbers")
    messagewrap = TFN(
        TFN(
            codeword,
            TFN(" ", comment="Single space"),
            numbers,
            comment="A single message"
        ),
        duplicity="+",
        separator=" ",
        key="messagewrap",
        saved=False,
        comment="Join message parts"
    )
    tree = TFN(
        callwrap,
        TFN(" ", comment="Single space"),
        messagewrap,
        comment="S28 style message"
    )
    return TF("Example format", tree), callwrap, call, messagewrap, codeword, numbers

@require_capability("admin")
@paginate(priyom.model.TransmissionFormat,
          25,
          ("display_name", "asc"),
          "page")
@router.route("/format", order=0)
@xsltea_site.with_template("view_formats.xml")
def view_formats(request: teapot.request.Request, page):
    formats = list(page)

    yield teapot.response.Response(None)
    yield {
        "formats": formats,
        "view_formats": view_formats,
        "add_format": edit_format,
        "edit_format": edit_format,
        "page": page,
    }, {}

@require_capability("admin")
@router.route("/format/{format_id:d}/edit",
              methods={teapot.request.Method.GET}, order=0)
@xsltea_site.with_template("format_form.xml")
def edit_format(request: teapot.request.Request, format_id=0):
    if format_id == 0:
        format = mdzhb_format()[0]
    else:
        format = request.dbsession.query(priyom.model.TransmissionFormat).get(
            format_id)

    form = priyom.logic.TransmissionFormatForm.initialize_from_database(
        format)

    yield teapot.response.Response(None)
    yield {
        "form": form
    }, {}

@require_capability("admin")
@router.route("/format/{format_id:d}/edit",
              methods={teapot.request.Method.POST})
@xsltea_site.with_template("format_form.xml")
def edit_format_POST(request: teapot.request.Request, format_id=0):
    post_data = request.post_data
    dbsession = request.dbsession

    form = priyom.logic.TransmissionFormatForm(
        post_data=post_data)

    target, action = form.find_action(post_data)
    if action == "update":
        pass
    elif hasattr(target, "parent") and target.parent:
        if action == "add_child":
            target.children.append(priyom.logic.TransmissionFormatRow())
        elif action == "move_up":
            i = target.index
            l = target.parent
            if i >= 1:
                l.pop(i)
                l.insert(i-1, target)
        elif action == "move_down":
            i = target.index
            l = target.parent
            if i < len(l):
                l.pop(i)
                l.insert(i+1, target)
        elif action == "delete":
            del target.parent[target.index]
    elif action == "save_to_db" and not form.errors:
        # FIXME: validate existing transmissions of this format before
        # continuing!

        try:
            format = form.to_database_object(
                destination=dbsession.query(priyom.model.TransmissionFormat).get(
                    format_id))
            dbsession.add(format)
            dbsession.commit()
        except sqlalchemy.exc.IntegrityError:
            dbsession.rollback()
        else:
            raise teapot.make_redirect_response(
                request,
                edit_format,
                format_id=format.id)

    template_args = {
        "form": form
    }

    yield teapot.response.Response(None)
    yield template_args, {}

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
    def id(self, value):
        if not value:
            return None
        return int(value)

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

@require_capability("admin")
@router.route("/station/{station_id:d}/edit", methods={
    teapot.request.Method.GET})
@xsltea_site.with_template("station_form.xml")
def edit_station(station_id, request: teapot.request.Request):
    station = request.dbsession.query(priyom.model.Station).get(station_id)
    form = StationForm(from_station=station)
    yield teapot.response.Response(None)

    yield {
        "form": form
    }, {}

@require_capability("admin")
@router.route("/station/{station_id:d}/edit",
              methods={teapot.request.Method.POST})
@xsltea_site.with_template("station_form.xml")
def edit_station_POST(station_id, request: teapot.request.Request):
    dbsession = request.dbsession
    station = dbsession.query(priyom.model.Station).get(station_id)
    form = StationForm(post_data=request.post_data)

    if station_id != form.id:
        form.errors[StationForm.id] = "Invalid ID"

    if not form.errors:
        station.enigma_id = form.enigma_id
        station.priyom_id = form.priyom_id
        station.nickname = form.nickname
        station.description = form.description
        station.status = form.status
        station.location = form.location
        dbsession.commit()

        raise teapot.make_redirect_response(
            request,
            edit_station,
            station_id=form.id)

    else:
        yield teapot.response.Response(None)
        yield {
            "form": form
        }, {}

@require_capability("admin")
@router.route("/station/{station_id:d}/delete", methods={
    teapot.request.Method.GET})
@xsltea_site.with_template("station_delete.xml")
def delete_station(station_id, request: teapot.request.Request):
    yield teapot.response.Response(None)
    yield {}, {}
