import collections

import teapot
import teapot.forms
import teapot.response
import teapot.request

import priyom.model
import priyom.logic

from .shared import *
from .auth import *

TFN_tuple = collections.namedtuple(
    "TFN_tuple",
    [
        "id",
        "order",
        "duplicity",
        "saved",
        "count",
        "content_match",
        "key",
        "join",
        "comment",
        "children",
        "level"
    ])

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
    return TF("", tree), callwrap, call, messagewrap, codeword, numbers

@require_capability("admin")
@router.route("/formats", order=0)
@xsltea_site.with_template("view_formats.xml")
def view_formats(request: teapot.request.Request):
    formats = list(request.dbsession.query(priyom.model.TransmissionFormat))

    yield teapot.response.Response(None)
    yield {
        "formats": formats,
        "add_format": edit_format,
        "edit_format": edit_format
    }, {}

@require_capability("admin")
@teapot.queryarg("id", "format_id", int, default=None)
@router.route("/formats/edit", methods={teapot.request.Method.GET}, order=0)
@xsltea_site.with_template("format_form.xml")
def edit_format(request: teapot.request.Request, format_id=None):
    if format_id is None:
        # format = mdzhb_format()[0]
        format = priyom.model.TransmissionFormat(
            "",
            priyom.model.TransmissionFormatNode())
    else:
        format = request.dbsession.query(priyom.model.TransmissionFormat).get(
            format_id)

    editee = priyom.logic.TransmissionFormatEditee.from_actual_format(format)

    yield teapot.response.Response(None)
    yield {
        "id": editee.id,
        "display_name": editee.display_name,
        "description": editee.description,
        "parsing_tree": editee.linearize_for_view()
    }, {}

@require_capability("admin")
@router.route("/formats/edit", methods={teapot.request.Method.POST})
@xsltea_site.with_template("format_form.xml")
def edit_format_POST(request: teapot.request.Request):
    postdata = request.post_data
    dbsession = request.dbsession

    root_node, by_index = _unlinearize_parsing_tree(postdata)

    try:
        action = next(iter(filter(lambda x: x.startswith("action:"), postdata.keys())))
    except StopIteration:
        action = "action:update"

    template_args = {}

    format_id = postdata["id"].pop()
    if not format_id or format_id == "None":
        format_id = None
    else:
        format_id = int(format_id)

    format_display_name = postdata["display_name"].pop()
    format_description = postdata["description"].pop()

    if action.startswith("action:node["):
        _, data = action.split("[", 1)
        node_index, action = data.split("]", 1)
        action = action[1:]

        if action == "add_child":
            node = by_index[int(node_index)]
            node.children.append(
                TFN_tuple(*([""]*(len(node)-1) + [node.level+1])))
        elif action == "delete":
            node = by_index[int(node_index)]
            parent = find_node_parent(root_node, node)
            if parent is not None:
                parent.children.remove(node)
        elif action == "move_up":
            node = by_index[int(node_index)]
            parent = find_node_parent(root_node, node)
            if parent is not None:
                idx = parent.children.index(node)
                if idx >= 1:
                    parent.children[idx] = parent.children[idx-1]
                    parent.children[idx-1] = node
        elif action == "move_down":
            node = by_index[int(node_index)]
            parent = find_node_parent(root_node, node)
            if parent is not None:
                idx = parent.children.index(node)
                if idx < len(parent.children)-1:
                    parent.children[idx] = parent.children[idx+1]
                    parent.children[idx+1] = node
    elif action == "action:save_to_db":
        try:
            tfn = try_conversion_to_db_objects(root_node, 0)
        except ValueError as err:
            _, node = err.args
            index = by_index.index(node)
            template_args["node_error_index"] = index
            template_args["node_error_message"] = str(err.__context__)

        if format_id is not None:
            format = dbsession.query(priyom.model.TransmissionFormat).get(
                format_id)
            format.display_name = format_display_name
            if format.root_node is not None:
                dbsession.delete(format.root_node)
            format.root_node = tfn
        else:
            format = priyom.model.TransmissionFormat(
                format_display_name, tfn)
            dbsession.add(format)
        format.description = format_description
        dbsession.commit()

        raise teapot.make_redirect_response(
            request, edit_format, format_id=format.id)


    template_args.update({
        "id": format_id,
        "display_name": format_display_name,
        "description": format_description,
        "parsing_tree": _linearize_parsing_tree(root_node)
    })

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
@router.route("/station/{station_id:d}/edit", methods={
    teapot.request.Method.POST})
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
