# encoding=utf8
from __future__ import unicode_literals, print_function, absolute_import

import operator
import re

from sqlalchemy import *
from sqlalchemy.orm import relationship, backref, validates

from . import base as base
from . import misc
from . import broadcast
from . import attachment

class TransmissionFormatNode(base.Base):
    __tablename__ = "transmission_format_nodes"

    DUPLICITY_ONE = "1"
    DUPLICITY_ONE_OR_MORE = "+"
    DUPLICITY_ZERO_OR_MORE = "*"
    DUPLICITY_FIXED = "{}"

    DUPLICITY_TEMPLATES = {
        DUPLICITY_ONE: "{match}",
        DUPLICITY_ONE_OR_MORE: "({match})+",
        DUPLICITY_ZERO_OR_MORE: "({match})*",
        DUPLICITY_FIXED: "({match}){{{count}}}"
    }
    DUPLICITY_JOIN_TEMPLATES = {
        #~ DUPLICITY_ONE: "(?P<{key0}>)(?P<{key1}>{match})",
        #~ DUPLICITY_ONE_OR_MORE: "(?P<{key0}>({match}{sep})*)(?P<{key1}>{match})",
        #~ DUPLICITY_ZERO_OR_MORE: "((?P<{key0}>({match}{sep})*)(?P<{key1}>{match}))?",
        #~ DUPLICITY_FIXED: "(?P<{key0}>({match}{sep}){{{count_minus_one}}})(?P<{key1}>{match})"
        DUPLICITY_ONE: "{match}",
        DUPLICITY_ONE_OR_MORE: "({match}{sep})*{match}",
        DUPLICITY_ZERO_OR_MORE: "(({match}{sep})*{match})?",
        DUPLICITY_FIXED: "({match}{sep}){{{count_minus_one}}}{match}"
    }

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("transmission_format_nodes.id"))
    order = Column(Integer)
    duplicity = Column(Enum(
        DUPLICITY_ONE,
        DUPLICITY_ONE_OR_MORE,
        DUPLICITY_ZERO_OR_MORE,
        DUPLICITY_FIXED
    ), nullable=False)
    saved = Column(Boolean, nullable=False)
    count = Column(Integer)
    content_match = Column(String(127))
    key = Column(String(63), nullable=True)
    join = Column(Boolean, nullable=False)

    children = relationship(
        "TransmissionFormatNode",
        backref=backref("parent", remote_side=[id])
    )

    def __init__(self, first_arg, *args, **kwargs):
        parent = kwargs.pop("parent", None)
        duplicity = kwargs.pop("duplicity", self.DUPLICITY_ONE)
        count = kwargs.pop("count", None)
        key = kwargs.pop("key", None)
        saved = kwargs.pop("saved", key is not None)
        separator = kwargs.pop("separator", None)
        join = kwargs.pop("join", separator is not None)

        super(TransmissionFormatNode, self).__init__(**kwargs)
        self.parent = parent
        if isinstance(first_arg, str):
            self.content_match = first_arg
            if len(args) > 0:
                raise TypeError("TransmissionFormatNode.__init__ takes one string argument or one or more node arguments")
        else:
            self.children.append(first_arg)
            for arg in args:
                self.children.append(arg)
            if separator is not None:
                self.content_match = separator
        self.duplicity = duplicity
        self.count = count
        self.key = key
        self.regex = None
        self.saved = saved
        self.join = join
        self.join_separator = None

    def _get_join_keys(self):
        return "jk"+str(id(self))+"k0", "jk"+str(id(self))+"k1"

    @validates('key')
    def validate_key(self, key, value):
        if value is None:
            return value
        if any(ord(x) > 127 or x == '<' or x == '>' for x in value):
            raise ValueError("key must be ASCII only, without < or >.")
        return value

    @validates('duplicity')
    def validate_duplicity(self, key, value):
        if value is not None and not value in self.DUPLICITY_TEMPLATES:
            raise KeyError("Invalid value for duplicity: {0!r}".format(value))
        return value

    @validates('count')
    def validate_count(self, key, count):
        if self.duplicity != self.DUPLICITY_FIXED:
            if count is not None:
                raise ValueError("Only NULL count is allowed for duplicity != fixed")
        else:
            if count is None:
                raise ValueError("NULL count is not allowed for duplicity == fixed")
        return count

    @validates('children')
    def validate_child(self, key, child):
        if child.order is None:
            try:
                max_order = max(map(operator.attrgetter("order"), self.children))
            except ValueError:
                max_order = -1
            child.order = max_order+1
        return child

    @validates('parent')
    def validate_parent(self, key, parent):
        if parent is not None:
            assert parent.content_match is None
        return parent

    @validates('content_match')
    def validate_content_match(self, key, content_match):
        try:
            re.compile(content_match)
        except re.error:
            raise ValueError("Supplied content_match is not a valid regular expression: {0!r}", content_match)
        return content_match

    def parse_subtree(self, message):
        regex = re.compile(self.build_inner_regex())
        results = []
        for match in regex.finditer(message):
            groupdict = match.groupdict()
            if not groupdict:
                results.append(message[match.start():match.end()])
            else:
                resultdict = {}
                for child in self.children:
                    child.propagate_parse(groupdict, resultdict)
                results.append(resultdict)
        return self, results

    def propagate_parse(self, groupdict, resultdict):
        if self.key is not None:
            result = self.parse_subtree(groupdict[self.key])
            resultdict[self.key] = result
        else:
            for child in self.children:
                child.propagate_parse(groupdict, resultdict)

    def parse(self, message):
        """
        Parse the message string *message* and return a intermediate
        representation of the message which can in turn be converted into a
        database tree.

        The structure is the following. For each keyed node, there is a tuple

            (node, items)

        where *node* is the node object itself and *items* is a list which
        contains the data matched by the node. If the node has a duplicity of
        one, the list contains exactly one item.

        *items* may either contain a string (for nodes without keyed children)
        or a dictionary mapping keys to tuples like the one above. The
        dictionary has exactly one entry for each keyed child.
        """
        return self.parse_subtree(message)[1][0]

    def build_inner_regex(self, keyed=True):
        if self.content_match is None or self.join:
            match = "".join(child.build_regex(keyed=keyed) for child in self.children)
        else:
            match = self.content_match
        return match

    def build_regex(self, keyed=True):
        match = self.build_inner_regex(keyed=keyed and self.key is None)
        if self.join:
            key0, key1 = self._get_join_keys()
            regex = self.DUPLICITY_JOIN_TEMPLATES[self.duplicity].format(
                match=match,
                key0=key0,
                key1=key1,
                count_minus_one=(self.count - 1) if self.count is not None else 0,
                sep=self.content_match
            )
        else:
            regex = self.DUPLICITY_TEMPLATES[self.duplicity].format(
                match=match,
                count=self.count
            )
        if self.key and keyed:
            regex = "(?P<{key}>{regex})".format(key=self.key, regex=regex)
        return regex

    def propagate_unparse(self, struct):
        for child in self.children:
            for item in child.unparse(struct):
                yield item

    def unparse_children(self, values):
        if not values:
            return
        if isinstance(values[0], str):
            for item in values:
                yield item
        else:
            for struct in values:
                yield "".join(self.propagate_unparse(struct))

    def unparse(self, struct):
        """
        Take a structure as generated by :meth:`parse` and unparse it into a
        string.

        Returns an iterable which can be joined to a string.
        """
        if self.key is not None:
            _, values = struct[self.key]
            assert _ is self

            if self.join:
                iterator = iter(self.unparse_children(values))
                yield next(iterator)
                for item in iterator:
                    yield self.join_separator or self.content_match
                    yield item
            else:
                for item in self.unparse_children(values):
                    yield item
        elif self.content_match is not None:
            yield self.content_match
        else:
            for item in self.propagate_unparse(struct):
                yield item

class TransmissionFormat(base.TopLevel):
    __tablename__ = "transmission_formats"

    id = Column(Integer, primary_key=True)
    display_name = Column(String(127), nullable=False)
    description = Column(Text)
    root_node_id = Column(Integer, ForeignKey(TransmissionFormatNode.id), nullable=False)

    root_node = relationship(TransmissionFormatNode)

    def __init__(self, display_name, root_node, description=None, **kwargs):
        super(TransmissionFormat, self).__init__(**kwargs)
        self.display_name = display_name
        self.root_node = root_node
        self.description = description

    def build_node_dict(self, curr, dct):
        if curr.key is not None:
            dct[curr.key] = (curr, len(dct))
            return
        for node in curr.children:
            self.build_node_dict(node, dct)

    def _build_tree_leaves(self, items, contents, parent):
        primitive_order = 0
        for key, (node, values) in items:
            for value in values:
                order = len(parent.children) if parent else primitive_order
                content_node = TransmissionContentNode(contents, node, order, value, parent=parent)
                primitive_order += 1

    def _build_tree_nodes(self, items, contents, parent):
        primitive_order = 0
        for key, (node, values) in items:
            for value in values:
                order = len(parent.children) if parent else primitive_order
                content_node = TransmissionContentNode(contents, node, order, None, parent=parent)
                self._build_tree(value, contents, content_node)
                primitive_order += 1

    def _build_tree(self, parse_result, contents, parent):
        items = sorted(parse_result.items(), key=lambda x: x[1][0].order)
        if not items:
            return
        if items[0][1][1] and isinstance(items[0][1][1][0], str):
            self._build_tree_leaves(items, contents, parent)
        else:
            self._build_tree_nodes(items, contents, parent)

    def parse(self, message):
        """
        Parse *message* and return a :cls:`TransmissionStructuredContents`
        instance which contains the keys from the parser tree associated with
        this format.

        Raises ValueError if the message cannot be parsed by this format.
        """
        result = self.root_node.parse(message)
        contents = TransmissionStructuredContents("text/plain", self)
        self._build_tree(result, contents, None)
        return contents

    def unparse(self, struct):
        """
        Unparse a previously parsed message. *struct* must be a structure as
        returned by :meth:`TransmissionFormatNode.parse`.

        Return the joined string containing the message represented by *struct*.
        """
        return "".join(self.root_node.unparse(struct))

    def __str__(self):
        return self.display_name.encode("utf-8")

    def __unicode__(self):
        return self.display_name


class Transmission(base.TopLevel):
    __tablename__ = "transmissions"

    id = Column(Integer, primary_key=True)
    broadcast_id = Column(Integer, ForeignKey(broadcast.Broadcast.id))
    timestamp = Column(DateTime, nullable=False)
    duration = Column(Integer, nullable=False)

    broadcast = relationship(broadcast.Broadcast, backref=backref("transmissions", order_by=timestamp))

class TransmissionContents(base.Base):
    __tablename__ = "transmission_contents"

    id = Column(Integer, primary_key=True)
    transmission_id = Column(Integer, ForeignKey(Transmission.id), nullable=False)
    mime = Column(String(127), nullable=False)
    is_transcribed = Column(Boolean, nullable=False)
    is_transcoded = Column(Boolean, nullable=False)
    alphabet_id = Column(Integer, ForeignKey(misc.Alphabet.id))
    attribution = Column(String(255), nullable=True)

    transmission = relationship(Transmission, backref=backref("contents"))
    alphabet = relationship(misc.Alphabet)

    def __init__(self, mime, is_transcribed=False,
            is_transcoded=False, transmission=None, alphabet=None,
            attribution=None):
        super(TransmissionContents, self).__init__()
        self.mime = mime
        self.is_transcribed = is_transcribed
        self.is_transcoded = is_transcoded
        self.alphabet = alphabet
        self.attribution = attribution

class TransmissionRawContents(TransmissionContents):
    __tablename__ = "transmission_raw_contents"
    __mapper_args__ = {"polymorphic_identity": "raw_contents"}

    id = Column(Integer, ForeignKey(TransmissionContents.id), primary_key=True)
    encoding = Column(String(63), nullable=False)
    contents = Column(Binary, nullable=True)

class TransmissionStructuredContents(TransmissionContents):
    __tablename__ = "transmission_structured_contents"
    __mapper_args__ = {"polymorphic_identity": "structured_contents"}

    id = Column(Integer, ForeignKey(TransmissionContents.id), primary_key=True)
    format_id = Column(Integer, ForeignKey(TransmissionFormat.id), nullable=False)

    format = relationship(TransmissionFormat)

    def __init__(self, mime, fmt, **kwargs):
        super(TransmissionStructuredContents, self).__init__(mime, **kwargs)
        self.format = fmt

    def unparse_struct(self):
        """
        Convert this message into a *struct* as required by
        :cls:`TransmissionFormat.unparse` recursively and return that structure.
        """
        result = {}
        for node in filter(lambda x: x.parent is None, self.nodes):
            _, child_list = result.setdefault(node.format_node.key, (node.format_node, []))
            child_list.append(node.unparse_struct())
        return result

    def unparse(self):
        """
        Return a string representation of this message.
        """
        return self.format.unparse(self.unparse_struct())

    def __unicode__(self):
        return self.unparse()

    def __str__(self):
        return unicode(self).encode("utf-8")


class TransmissionContentNode(base.Base):
    __tablename__ = "transmission_content_nodes"

    id = Column(Integer, primary_key=True)
    content_id = Column(Integer, ForeignKey(TransmissionStructuredContents.id), nullable=False)
    parent_id = Column(Integer, ForeignKey(__tablename__ + ".id"), nullable=True)
    format_node_id = Column(Integer, ForeignKey(TransmissionFormatNode.id), nullable=False)
    order = Column(Integer, nullable=False)
    segment = Column(Binary, nullable=False)

    children = relationship(
        "TransmissionContentNode",
        backref=backref("parent", remote_side=[id])
    )
    format_node = relationship(TransmissionFormatNode)
    contents = relationship(TransmissionStructuredContents, backref=backref("nodes", order_by=order))

    def __init__(self, structured_contents, format_node, order, segment,
            parent=None, **kwargs):
        super(TransmissionContentNode, self).__init__(**kwargs)
        self.contents = structured_contents
        self.format_node = format_node
        self.order = order
        self.segment = segment
        self.parent = parent

    def unparse_struct(self):
        """
        Return an element of the values list in the structure required by
        :cls:`TransmissionFormat.unparse`. This is not of much use if called
        directly but is used by :cls:`TransmissionStructuredContents.unparse`.
        """
        if len(self.children) > 0:
            result = {}
            for child in self.children:
                _, child_list = result.setdefault(child.format_node.key, (child.format_node, []))
                child_list.append(child.unparse_struct())
            return result
        else:
            return self.segment

class TransmissionAttachment(attachment.Attachment):
    __tablename__ = "transmission_attachments"
    __mapper_args__ = {"polymorphic_identity": "transmission_attachment"}

    attachment_id = Column(Integer, ForeignKey(attachment.Attachment.id), primary_key=True)
    transmission_id = Column(Integer, ForeignKey(Transmission.id), nullable=False)
    relation = Column(Enum(
        "recording",
        "waterfall"
    ))

    transmission = relationship(Transmission, backref=backref("attachments"))
