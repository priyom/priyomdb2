# encoding=utf8
from __future__ import unicode_literals, print_function, absolute_import

import abc
import operator
import re

from sqlalchemy import *
from sqlalchemy.orm import relationship, backref, validates, Session

from .base import Base, TopLevel
from .event import Event
from .attachment import Attachment

def make_regex_range(nmin, nmax):
    if nmax is None:
        if nmin == 1:
            return "+"
        elif nmin == 0:
            return "*"
    elif nmax == 1:
        if nmin == 0:
            return "?"
        elif nmin == 1:
            return ""

    return "{{{nmin},{nmax}}}".format(
        nmin=nmin,
        nmax=nmax if nmax is not None else ""
    )

def regex_range(regex_to_range, nmin, nmax, omit_grouping=False):
    nmin = max(nmin, 0)
    if nmax is not None:
        nmax = max(nmax, 0)

    if nmin == nmax == 0:
        return ""
    elif nmin == nmax == 1:
        return regex_to_range

    if not omit_grouping:
        regex_to_range = "(?:" + regex_to_range + ")"

    return regex_to_range + make_regex_range(nmin, nmax)

class Alphabet(Base):
    __tablename__ = 'alphabets'
    __table_args__ = (
        UniqueConstraint('short_name'),
        UniqueConstraint('display_name'),
        Base.__table_args__
    )

    id = Column(Integer, primary_key=True)
    short_name = Column(Unicode(10), nullable=False)
    display_name = Column(Unicode(127), nullable=False)

    def __init__(self, short_name, display_name):
        super(Alphabet, self).__init__()
        self.short_name = short_name
        self.display_name = display_name

class FormatNode(Base):
    TAG_PLAIN = "plain"
    TAG_FLATTENABLE = "flattenable"
    TAG_RSN = "rsn"

    __tablename__ = "format_node"

    id = Column(Integer, primary_key=True)
    type_ = Column(Unicode(4))
    order = Column(Integer, nullable=False)

    parent_id = Column(Integer,
                       ForeignKey(
                           "format_structure_node.id",
                           ondelete="CASCADE",
                           name="format_node_fk_format_structure_node_id"),
                       nullable=True)
    parent = relationship(
        "FormatStructure",
        backref=backref("children",
                        passive_deletes=True,
                        order_by="FormatNode.order"),
        foreign_keys=[parent_id])

    __table_args__ = (
        # UniqueConstraint("parent_id", "order"),
        Base.__table_args__
    )

    __mapper_args__ = {
        "polymorphic_identity": "node",
        "polymorphic_on": type_,
        "with_polymorphic": "*"
    }

    def __init__(self, *, order=None, parent=None):
        super().__init__()
        if parent is not None and order is None and parent.children:
            order = parent.children[-1].order + 1
        self.parent = parent
        self.order = order or 0

    @abc.abstractmethod
    def get_outer_regex(self):
        """
        Return a string resembling the minimum regex required to validate and
        parse this format node.
        """

    def parse(self, text):
        raise NotImplementedError("Cannot parse this node standalone.")

    def unparse(self, data):
        """
        Unparse a list of parser statements.

        This is the same kind of list as returned by :meth:`parse`.
        """
        raise NotImplementedError("Cannot unparse this node standalone.")

class FormatStructure(FormatNode):
    __tablename__ = "format_structure_node"

    __mapper_args__ = {
        "polymorphic_identity": "srct",
        "inherit_condition": id == FormatNode.id,
    }

    id = Column(Integer,
                ForeignKey(FormatNode.id,
                           ondelete="CASCADE",
                           name="format_structure_node_fk_format_node_id"),
                primary_key=True)
    joiner_regex = Column(Unicode(255), nullable=True)
    joiner_const = Column(Unicode(255), nullable=True)
    save_to = Column(Unicode(255), nullable=True)
    nmin = Column(Integer, nullable=False)
    nmax = Column(Integer, nullable=True)

    def __init__(self, *children,
                 joiner=None, joiner_regex=None,
                 save_to=None,
                 nmin=1, nmax=1, **kwargs):
        super().__init__(**kwargs)
        self.joiner_const = joiner
        self.joiner_regex = joiner_regex or joiner
        self.save_to = save_to
        self.nmin = nmin
        self.nmax = nmax
        self.children.extend(children)

    def __repr__(self):
        return ("<FormatStructure order={} #children={} nmin={} nmax={} "
                "save_to={!r} joiner={!r}/{!r}>".format(
                    self.order,
                    len(self.children),
                    self.nmin,
                    self.nmax,
                    self.save_to,
                    self.joiner_const,
                    self.joiner_regex))

    def _get_compound_outer_child_regex(self):
        return "".join(child.get_outer_regex()
                       for child in self.children)

    def _get_compound_inner_child_regex(self):
        return "".join(
            r"(?P<c{idx}>{regex})".format(
                idx=i,
                regex=child.get_outer_regex())
            for i, child in enumerate(self.children))

    def get_outer_regex(self):
        children_regex = self._get_compound_outer_child_regex()

        if self.nmin == 1 and self.nmax == 1:
            regex = children_regex
        elif not self.joiner_regex:
            # the simple case. we just emit the correct constraint
            regex = regex_range(children_regex,
                                self.nmin,
                                self.nmax)
        else:
            # this is the complex case. we have to take into account joiners
            regex = (regex_range(children_regex + self.joiner_regex,
                                 self.nmin-1,
                                 (self.nmax-1)
                                 if self.nmax is not None
                                 else None) +
                     children_regex)

        return regex

    def _rewrite_parent(self, statement_generator):
        for destination, _, text in statement_generator:
            yield destination, self, text

    def _parse_match(self, match):
        # if we are a saving node, we have to emit save statements
        # otherwise, we delegate parsing to the child nodes

        match_text = match.string[match.start():match.end()]

        if self.save_to:
            yield (self, None, match_text)
            return

        if not self.nmin == self.nmax == 1:
            def child_statements(child, group):
                return self._rewrite_parent(child.parse(group))
        else:
            def child_statements(child, group):
                return child.parse(group)

        # as a non-saving node, we have to figure out whether we are the common
        # parent which needs to take ownership of the statements emitted from
        # the children.
        groupdict = match.groupdict()
        for i, child in enumerate(self.children):
            group = groupdict["c"+str(i)]
            yield from child_statements(child, group)

    def parse(self, text):
        regex = re.compile(self._get_compound_inner_child_regex())
        for match in regex.finditer(text):
            yield from self._parse_match(match)

    def unparse(self, data):
        items = []
        if self.save_to:
            # expect data addressed to me
            # make sure we don’t consume more than the maximum amount of items
            # (we are not strict about the minimum though)
            # print("searching for data")
            # print(self)
            while (self.nmax is None or len(items) < self.nmax) and data:
                addressee, _, text = data[0]
                # print(addressee, _, text)
                if addressee is not self:
                    break
                data.pop(0)
                items.append(text)
        else:
            # delegate to children
            while (self.nmax is None or len(items) < self.nmax) and data:
                items.append("".join(child.unparse(data)
                                     for child in self.children))

        # recompose
        return (self.joiner_const or "").join(items)


class FormatSimpleContent(FormatNode):
    KIND_ALPHABET_CHARACTER = "alphabet_character"
    KIND_DIGIT = "digit"
    KIND_ALPHANUMERIC = "alphanumeric"
    KIND_NONSPACE = "nonspace"
    KIND_SPACE = "space"

    KINDS = {
        KIND_ALPHANUMERIC: (r"[\d\w?]", "X"),
        KIND_ALPHABET_CHARACTER: (r"[\w?]", "A"),
        KIND_DIGIT: (r"[\d?]", "#"),
        KIND_NONSPACE: (r"\S", "?"),
        KIND_SPACE: (r"\s", " "),
    }

    __tablename__ = "format_simple_content_node"

    __mapper_args__ = {
        "polymorphic_identity": "sicn"
    }

    id = Column(Integer,
                ForeignKey(FormatNode.id,
                           ondelete="CASCADE",
                           name="format_structure_node_fk_format_node_id"),
                primary_key=True)
    kind = Column(
        Enum(
            *KINDS,
            name="simple_content_kind"
        ),
        nullable=False)
    nmin = Column(Integer, nullable=False)
    nmax = Column(Integer, nullable=True)

    def __init__(self, kind, *, nmin=1, nmax=None, **kwargs):
        super().__init__(**kwargs)
        if kind not in self.KINDS:
            raise ValueError("Invalid simple content type: {!r}".format(kind))
        self.kind = kind
        self.nmin = nmin
        self.nmax = nmax

    def __repr__(self):
        return ("<FormatSimpleContentNode order={} kind={} "
                "nmin={} nmax={}>".format(
                    self.order,
                    self.kind,
                    self.nmin,
                    self.nmax))

    def get_outer_regex(self):
        return regex_range(
            self.KINDS[self.kind][0],
            self.nmin,
            self.nmax,
            omit_grouping=True)

    def parse(self, text):
        regex = re.compile("^"+self.get_outer_regex()+"$")
        if not regex.match(text):
            raise ValueError("Match failed at {} with {!r}".format(
                self, text))

        return []

    def unparse(self, data):
        return self.KINDS[self.kind][1] * self.nmin


class Format(TopLevel):
    __tablename__ = "formats"

    id = Column(Integer, primary_key=True)
    display_name = Column(Unicode(255), nullable=False)
    description = Column(UnicodeText, nullable=False)

    root_node_id = Column(Integer,
                          ForeignKey(
                              FormatStructure.id,
                              ondelete="RESTRICT",
                              name="formats_fk_format_structure_node_id"),
                          nullable=False)

class TransmissionContents(Base):
    __tablename__ = "transmission_contents"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer,
                      ForeignKey(Event.id,
                                 ondelete="CASCADE"),
                      nullable=False)
    mime = Column(Unicode(127), nullable=False)
    is_transcribed = Column(Boolean, nullable=False)
    is_transcoded = Column(Boolean, nullable=False)
    alphabet_id = Column(Integer, ForeignKey(Alphabet.id))
    attribution = Column(Unicode(255), nullable=True)
    subtype = Column(Unicode(50), nullable=False)

    parent_contents_id = Column(Integer,
                                ForeignKey("transmission_contents.id",
                                           ondelete="CASCADE"),
                                nullable=True)
    parent_contents = relationship("TransmissionContents",
                                   backref=backref("children",
                                                   passive_deletes=True),
                                   foreign_keys=[parent_contents_id],
                                   remote_side=[id])

    event = relationship(Event,
                         backref=backref(
                             "contents",
                             cascade="all, delete-orphan",
                             passive_deletes=True))
    alphabet = relationship(Alphabet)

    __mapper_args__ = {
        "polymorphic_identity": "transmission_contents",
        "polymorphic_on": subtype
    }

    def __init__(self, mime, is_transcribed=False,
            is_transcoded=False, alphabet=None,
            attribution=None):
        super(TransmissionContents, self).__init__()
        self.mime = mime
        self.is_transcribed = is_transcribed
        self.is_transcoded = is_transcoded
        self.alphabet = alphabet
        self.attribution = attribution

    def short_str(self, max_len=140, ellipsis="…"):
        s = str(self)
        if len(s) > max_len:
            s = s[:max_len-len(ellipsis)] + ellipsis
        return s

class TransmissionRawContents(TransmissionContents):
    __tablename__ = "transmission_raw_contents"
    __mapper_args__ = {"polymorphic_identity": "raw_contents"}

    id = Column(Integer,
                ForeignKey(TransmissionContents.id,
                           ondelete="CASCADE"),
                primary_key=True)
    encoding = Column(Unicode(63), nullable=False)
    contents = Column(Binary, nullable=True)

    def __str__(self):
        if self.encoding != "binary":
            return self.contents.decode(self.encoding)
        return "binary blob"

class TransmissionStructuredContents(TransmissionContents):
    __tablename__ = "transmission_structured_contents"
    __mapper_args__ = {"polymorphic_identity": "structured_contents"}

    id = Column(Integer,
                ForeignKey(TransmissionContents.id,
                           ondelete="CASCADE"),
                primary_key=True)
    format_id = Column(Integer,
                       ForeignKey(Format.id,
                                  ondelete="CASCADE"),
                       nullable=False)

    format = relationship(Format)

    def __init__(self, mime, fmt, **kwargs):
        super().__init__(mime, **kwargs)
        self.format = fmt

    def unparse_struct(self):
        """
        Convert this message into a *struct* as required by
        :cls:`Format.unparse` recursively and return that structure.
        """
        result = {}
        for node in filter(lambda x: x.parent is None, self.nodes):
            _, child_list = result.setdefault(
                node.format_node.key, (node.format_node, []))
            child_list.append(node.unparse_struct())
        return result

    def unparse(self):
        """
        Return a string representation of this message.
        """
        return self.format.unparse(self.unparse_struct())

    def __str__(self):
        return self.unparse()


class TransmissionContentNode(Base):
    __tablename__ = "transmission_content_nodes"

    id = Column(Integer, primary_key=True)
    content_id = Column(Integer,
                        ForeignKey(TransmissionStructuredContents.id,
                                   ondelete="CASCADE"),
                        nullable=False)
    parent_id = Column(Integer,
                       ForeignKey(__tablename__ + ".id",
                                  ondelete="CASCADE"),
                       nullable=True)
    format_node_id = Column(Integer,
                            ForeignKey(FormatNode.id,
                                       ondelete="CASCADE"),
                            nullable=False)
    order = Column(Integer, nullable=False)
    segment = Column(Unicode(127))

    children = relationship(
        "TransmissionContentNode",
        backref=backref("parent",
                        remote_side=[id]),
        passive_deletes=True,
        cascade="all, delete-orphan",
        lazy="joined",
        join_depth=4
    )
    format_node = relationship(FormatNode)
    contents = relationship(TransmissionStructuredContents,
                            backref=backref("nodes",
                                            order_by=order,
                                            passive_deletes=True))

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
        :cls:`Format.unparse`. This is not of much use if called
        directly but is used by :cls:`TransmissionStructuredContents.unparse`.
        """
        if len(self.children) > 0:
            result = {}
            for child in self.children:
                _, child_list = result.setdefault(
                    child.format_node.key, (child.format_node, []))
                child_list.append(child.unparse_struct())
            return result
        else:
            return self.segment

class EventAttachment(Attachment):
    __tablename__ = "event_attachments"
    __mapper_args__ = {"polymorphic_identity": "transmission_attachment"}

    attachment_id = Column(Integer, ForeignKey(Attachment.id), primary_key=True)
    event_id = Column(Integer,
                      ForeignKey(Event.id,
                                 ondelete="CASCADE"),
                      nullable=False)
    relation = Column(Enum(
        "recording",
        "waterfall"
    ))

    event = relationship(Event,
                         backref=backref("attachments",
                                         passive_deletes=True))
