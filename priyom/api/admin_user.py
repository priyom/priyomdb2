import collections

import teapot
import teapot.response
import teapot.request

import priyom.model

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

def _linearize_parsing_tree(node, level=0, index=0):
    yield (level, node, index)
    index += 1
    for child in node.children:
        index = yield from _linearize_parsing_tree(child, level+1, index)
    return index

def _reconstruct_node(postdata, index):

    def attr(name):
        return postdata.pop("node[{}].{}".format(index, name)).pop()

    def boolattr(name):
        try:
            postdata.pop("node[{}].{}".format(index, name))
            return True
        except KeyError:
            return False

    node = TFN_tuple(
        id=attr("id"),
        order=index,
        duplicity=attr("duplicity"),
        saved=boolattr("saved"),
        count=attr("count"),
        content_match=attr("content_match"),
        key=attr("key"),
        join=boolattr("join"),
        comment=attr("comment"),
        children=[],
        level=int(attr("level")))
    return node

def _unlinearize_parsing_subtree(postdata, parent, index, by_index=[]):
    try:
        node = _reconstruct_node(postdata, index)
    except KeyError:
        return None, index
    while node:
        if parent.level == node.level-1:
            parent.children.append(node)
            by_index.append(node)
        else:
            return node, index

        node, index = _unlinearize_parsing_subtree(
            postdata, node, index+1,
            by_index)
    return None, index

def _unlinearize_parsing_tree(postdata):
    root_node = _reconstruct_node(postdata, 0)
    by_index = [root_node]
    _unlinearize_parsing_subtree(postdata, root_node, 1, by_index)
    return root_node, by_index

def find_node_parent(parent, node):
    for child in parent.children:
        if child is node:
            return parent
        result = find_node_parent(child, node)
        if result is not None:
            return result

def try_conversion_to_db_objects(node, index):
    try:
        tfn = priyom.model.TransmissionFormatNode()
        tfn.duplicity = node.duplicity
        if tfn.duplicity == priyom.model.TransmissionFormatNode.DUPLICITY_FIXED:
            tfn.count = int(node.count)
        tfn.order = index
        tfn.content_match = node.content_match
        tfn.key = node.key
        tfn.comment = node.comment
        tfn.join = bool(node.join)
        tfn.saved = bool(node.saved)
    except ValueError as err:
        raise ValueError("could not convert node", node) from err
    child_nodes = list(
        try_conversion_to_db_objects(node, index)
        for index, node in enumerate(node.children))
    tfn.children.extend(child_nodes)
    return tfn

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
    root_node = format.root_node

    yield teapot.response.Response(None)
    yield {
        "id": str(format.id),
        "display_name": format.display_name,
        "description": format.description,
        "parsing_tree": _linearize_parsing_tree(root_node)
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

@router.route("/station/{station_id:d}/edit", methods={
    teapot.request.Method.GET})
@xsltea_site.with_template("station_form.xml")
def edit_station(station_id, request: teapot.request.Request):
    station = request.dbsession.query(priyom.model.Station).get(station_id)
    yield teapot.response.Response(None)

    yield {
        "station": station
    }, {}
