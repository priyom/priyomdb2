# encoding=utf8
from __future__ import unicode_literals, print_function, absolute_import

import abc
import binascii
import operator
import re
import sys

from sqlalchemy import *
from sqlalchemy.orm import relationship, backref, validates, Session

from .base import Base, TopLevel
from .event import Event
from .attachment import Attachment
from .format import Format, FormatNode

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

class Contents(Base):
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
    parent_contents = relationship("Contents",
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
        super().__init__()
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

class FreeTextContents(Contents):
    __tablename__ = "transmission_freetext_contents"
    __mapper_args__ = {"polymorphic_identity": "txtc"}

    id = Column(Integer,
                ForeignKey(Contents.id,
                           ondelete="CASCADE"),
                primary_key=True)
    contents = Column(Text, nullable=True)

    def __init__(self, mime, contents, *args, **kwargs):
        super().__init__(mime, *args, **kwargs)
        self.contents = contents

    def __str__(self):
        return self.contents

class BinaryContents(Contents):
    __tablename__ = "transmission_raw_contents"
    __mapper_args__ = {"polymorphic_identity": "binc"}

    id = Column(Integer,
                ForeignKey(Contents.id,
                           ondelete="CASCADE"),
                primary_key=True)
    contents = Column(Binary, nullable=True)

    def __init__(self, mime, contents, *args, **kwargs):
        super().__init__(mime, *args, **kwargs)
        self.contents = contents

    def __str__(self):
        return binascii.b2a_hex(self.contents)

class StructuredContents(Contents):
    __tablename__ = "transmission_structured_contents"
    __mapper_args__ = {"polymorphic_identity": "structured_contents"}

    id = Column(Integer,
                ForeignKey(Contents.id,
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

    def __str__(self):
        return self.format.unparse(self.nodes)


class ContentNode(Base):
    __tablename__ = "transmission_content_nodes"

    id = Column(Integer, primary_key=True)
    content_id = Column(Integer,
                        ForeignKey(StructuredContents.id,
                                   ondelete="CASCADE"),
                        nullable=False)
    format_node_id = Column(Integer,
                            ForeignKey(FormatNode.id,
                                       ondelete="CASCADE"),
                            nullable=False)
    order = Column(Integer, nullable=False)
    child_number = Column(Integer, nullable=False)
    segment = Column(Unicode(127))

    format_node = relationship(FormatNode)
    contents = relationship(StructuredContents,
                            backref=backref("nodes",
                                            order_by=order,
                                            passive_deletes=True))

    def __init__(self, order, child_number, format_node, segment, **kwargs):
        super(ContentNode, self).__init__(**kwargs)
        self.order = order
        self.child_number = child_number
        self.format_node = format_node
        self.segment = segment

    def __eq__(self, other):
        return ((self.order, self.child_number, self.segment) ==
                (other.order, other.child_number, other.segment) and
                self.format_node is other.format_node)

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return ("<ContentNode order={} child_number={} segment={!r}"
                " format_node={!r}>").format(
                    self.order,
                    self.child_number,
                    self.segment,
                    self.format_node)


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
