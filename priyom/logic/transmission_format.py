"""
This file deals with the logic needed to manipulate transmission formats. This
includes a serialization suitable to render an HTML table and to perform easy
manipulations without having to care about the peculiarities of a tree
structure.
"""
import collections
import functools
import itertools
import weakref

import priyom.model

__all__ = [
    "TransmissionFormatEditee"]

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


def _row_from_postdata(postdata, index):
    def attr(name, allow_none=False):
        try:
            v = postdata["node[{}].{}".format(index, name)].pop()
        except (KeyError, IndexError) as err:
            raise KeyError("node[{}].{}".format(index, name)) from err
        if not v and allow_none:
            return None
        return v

    def boolattr(name):
        try:
            postdata["node[{}].{}".format(index, name)]
            return True
        except (KeyError, ValueError, IndexError):
            return False

    def intattr(name):
        try:
            return int(attr(name))
        except ValueError as err:
            raise ValueError(str(err), name, index)

    return TFN_tuple(
        id=attr("id", allow_none=True),
        order=index,
        duplicity=attr("duplicity"),
        saved=boolattr("saved"),
        count=attr("count", allow_none=True),
        content_match=attr("content_match", allow_none=True),
        key=attr("key", allow_none=True),
        join=boolattr("join"),
        comment=attr("comment", allow_none=True),
        children=[],
        level=intattr("level"))

def rows_from_postdata(postdata):
    try:
        for index in itertools.count():
            yield _row_from_postdata(postdata, index)
    except KeyError:
        pass

def convert_node(level, node, with_children=True):
    return TFN_tuple(
        id=str(node.id),
        order=node.order,
        duplicity=node.duplicity,
        saved=node.saved,
        count=node.count,
        content_match=node.content_match,
        key=node.key,
        join=node.join,
        comment=node.comment,
        children=list(map(
            functools.partial(convert_node, level+1),
            node.children)) if with_children else [],
        level=level)

def flatten_tree(level, node):
    yield convert_node(level, node, False)
    for child in node.children:
        yield from flatten_tree(level+1, child)

class TransmissionFormatEditee:
    @classmethod
    def from_postdata(cls, postdata):
        return cls(
            postdata["id"].pop(),
            postdata["display_name"].pop(),
            postdata["description"].pop(),
            rows_from_postdata(postdata))

    @classmethod
    def from_actual_format(cls, transmission_format):
        return cls(
            str(transmission_format.id) \
                if transmission_format.id is not None
                else ""
            ,
            transmission_format.display_name,
            transmission_format.description,
            flatten_tree(0, transmission_format.root_node))

    def __init__(self, id, display_name, description, rows):
        super().__init__()
        self.id = id
        self.display_name = display_name
        self.description = description
        self.root = self.fill_tree(rows)

    def add_child(self, to_parent):
        to_parent.children.append(
            TFN_tuple(*([""]*len(to_parent)-1) + [to_parent.level+1]))

    def delete_node(self, node):
        i, parent = self.find_node_parent(node)
        if parent is None:
            raise ValueError("node not in tree or is root node")
        del parent.children[i]

    def fill_tree(self, rows):
        byindex = {}
        rowiter = iter(rows)
        parentstack = []
        try:
            currparent = next(rowiter)
        except StopIteration:
            raise ValueError("Transmission formats require at least one node")
        prevnode = currparent
        byindex[0] = prevnode
        for i, node in enumerate(rowiter):
            if node.level == currparent.level+1:
                pass
            elif node.level == prevnode.level+1:
                parentstack.append(currparent)
                currparent = prevnode
            elif node.level <= currparent.level:
                while node.level < currparent.level+1:
                    try:
                        currparent = parentstack.pop()
                    except IndexError as err:
                        raise ValueError("Inconsistency in level values (no"
                                         "elements left in parent stack)") \
                            from err
            else:
                raise ValueError("Inconsistency in level values (intermediate"
                                 " level missing")

            currparent.children.append(node)
            prevnode = node
            byindex[i+1] = node

        self.byindex = byindex
        return currparent

    def find_node_parent(self, node, within=None):
        within = within or self.root
        for i, child in enumerate(within.children):
            if child is node:
                return i, within
            match = self.find_node_parent(node, within=child)
            if match is not None:
                return match
        return -1, None

    def _linearize_for_view(self, level, parent):
        parent = parent or self.root
        yield level, parent
        for child in parent.children:
            yield from self._linearize_for_view(
                level+1,
                child)

    def linearize_for_view(self):
        return (
            (i, l, n)
            for i, (l, n) in enumerate(self._linearize_for_view(0, self.root)))

    def move_down(self, node):
        i, parent = self.find_node_parent(node)
        if parent is None:
            raise ValueError("node not in tree or is root node")

        if i == len(parent.children)-1:
            return

        parent.children[i] = parent.children[i+1]
        parent.children[i+1] = node

    def move_up(self, node):
        i, parent = self.find_node_parent(node)
        if parent is None:
            raise ValueError("node not in tree or is root node")

        if i == 0:
            return

        parent.children[i] = parent.children[i-1]
        parent.children[i-1] = node

    def node_by_index(self, index):
        return self.byindex[index]

    @classmethod
    def _node_to_object(cls, node, order):
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
            cls._node_to_object(node, index)
            for index, node in enumerate(node.children))
        tfn.children.extend(child_nodes)
        return tfn

    def to_objects(self, existing_format=None):
        rootnode = self._node_to_object(self.root, 0)
        if existing_format is not None:
            format = priyom.model.TransmissionFormat(
                self.display_name, rootnode, self.description)
        else:
            existing_format.display_name = self.display_name
            existing_format.root_node = rootnode
            existing_format.description = description
            format = existing_format

        return format
