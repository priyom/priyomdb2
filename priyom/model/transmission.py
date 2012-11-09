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

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("transmission_format_nodes.id"))
    order = Column(Integer)
    duplicity = Column(Enum(
        DUPLICITY_ONE,
        DUPLICITY_ONE_OR_MORE,
        DUPLICITY_ZERO_OR_MORE,
        DUPLICITY_FIXED
    ), nullable=False)
    count = Column(Integer)
    content_match = Column(String(127))
    key = Column(String(63), nullable=True)

    children = relationship(
        "TransmissionFormatNode",
        backref=backref("parent", remote_side=[id])
    )

    def __init__(self, first_arg, *args, **kwargs):
        try:
            parent = kwargs.pop("parent")
        except KeyError:
            parent = None
        try:
            duplicity = kwargs.pop("duplicity")
        except KeyError:
            duplicity = self.DUPLICITY_ONE
        try:
            count = kwargs.pop("count")
        except KeyError:
            count = None
        try:
            key = kwargs.pop("key") or None
        except KeyError:
            key = None

        super(TransmissionFormatNode, self).__init__(**kwargs)
        self.parent = parent
        if isinstance(first_arg, basestring):
            self.content_match = first_arg
            if len(args) > 0:
                raise TypeError("TransmissionFormatNode.__init__ takes one string argument or one or more node arguments")
        else:
            self.children.append(first_arg)
            for arg in args:
                self.children.append(arg)
        self.duplicity = duplicity
        self.count = count
        self.key = key
        self.regex = None

    @validates('key')
    def validate_key(self, key, value):
        if value is None:
            return value
        if len(filter(lambda x: ord(x) > 127 or x == '<' or x == '>', value)) > 0:
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

    def build_inner_regex(self):
        if self.content_match is None:
            match = "".join(map(TransmissionFormatNode.build_regex, self.children))
        else:
            match = self.content_match
        return match

    def build_regex(self):
        match = self.build_inner_regex()
        regex = self.DUPLICITY_TEMPLATES[self.duplicity].format(
            match=match,
            count=self.count
        )
        if self.key:
            regex = "(?P<{key}>{regex})".format(key=self.key, regex=regex)
        return regex

    def unparse_content(self, keymap):
        if self.key is None:
            yield self.content_match
            return

        instance_values = keymap[self.key]
        if self.duplicity == self.DUPLICITY_ONE:
            if len(instance_values) != 1:
                raise ValueError(
                    "Exactly one value required for key {0!r} (got {1})".format(
                        self.key,
                        len(instance_values)
                    )
                )
        elif self.duplicity == self.DUPLICITY_ONE_OR_MORE:
            if len(instance_values) < 1:
                raise ValueError(
                    "Too few values for key {0!r} (got {1}, need at least one)".format(
                        self.key,
                        len(instance_values)
                    )
                )
        elif self.duplicity == self.DUPLICITY_FIXED:
            if len(instance_values) < 1:
                raise ValueError(
                    "Exactly {2} values for key {0!r} required (got {1})".format(
                        self.key,
                        len(instance_values),
                        self.count
                    )
                )
        for item in instance_values:
            yield item

    def unparse(self, keymap):
        if self.content_match is not None or self.key is not None:
            for item in self.unparse_content(keymap):
                yield item
            return

        for child in self.children:
            for segment in child.unparse(keymap):
                yield segment

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

    def parse_raw(self, message):
        """
        Parse *message* and return a list which consists of tuples of the
        matching keyed :cls:`TransmissionFormatNode` and the matched strings.

        Raises ValueError if the message cannot be parsed by this format.
        """
        regex = re.compile(self.root_node.build_regex())
        m = regex.match(message)
        if m is None:
            raise ValueError("{0!r} is not a valid {1!s} message".format(
                message,
                self
            ))
        node_dict = {}
        # FIXME: do that only when neccessary
        self.build_node_dict(self.root_node, node_dict)

        for key, value in m.groupdict().items():
            node, order = node_dict[key]
            regex = re.compile(node.build_inner_regex())
            matches = list(map(lambda x: value[x.start():x.end()], regex.finditer(value)))
            yield order, node, matches

    def parse(self, message):
        """
        Parse *message* and return a :cls:`TransmissionStructuredContents`
        instance which contains the keys from the parser tree associated with
        this format.

        Raises ValueError if the message cannot be parsed by this format.
        """
        sorted_result = sorted( self.parse_raw(message),
                                key=operator.itemgetter(0))
        contents = TransmissionStructuredContents("text/plain", self)
        order = 0
        for _, node, matches in sorted_result:
            for match in matches:
                content_node = TransmissionContentNode(
                    contents,
                    node,
                    order,
                    match
                )
                order += 1
        return contents

    def unparse(self, keymap):
        """
        Unparse a previously parsed message whose important information is
        stored in *keymap*.

        *keymap* must be a mapping which maps :cls:`TransmissionFormatNode` keys
        to a list of values, which is in the order of occurence in the original
        pattern.

        Returns a string, which is in turn parsable by this format and which
        will yield exactly the same information.

        This will raise a :cls:`KeyError` if the keymap is missing a key defined
        by this format.
        """
        return "".join(self.root_node.unparse(keymap))

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

    def unparse(self):
        # put our nodes in a handy structure
        keymap = {}
        for node in self.nodes:
            keymap.setdefault(node.format_node.key, []).append(node.segment)

        return self.format.unparse(keymap)


class TransmissionContentNode(base.Base):
    __tablename__ = "transmission_content_nodes"

    id = Column(Integer, primary_key=True)
    content_id = Column(Integer, ForeignKey(TransmissionStructuredContents.id), nullable=False)
    format_node_id = Column(Integer, ForeignKey(TransmissionFormatNode.id), nullable=False)
    order = Column(Integer, nullable=False)
    segment = Column(Binary, nullable=False)

    format_node = relationship(TransmissionFormatNode)
    contents = relationship(TransmissionStructuredContents, backref=backref("nodes", order_by=order))

    def __init__(self, structured_contents, format_node, order, segment):
        super(TransmissionContentNode, self).__init__()
        self.contents = structured_contents
        self.format_node = format_node
        self.order = order
        self.segment = segment

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
