# encoding=utf8
from __future__ import unicode_literals, print_function, absolute_import

from sqlalchemy import *
from sqlalchemy.orm import relationship, backref, validates

from . import base as base
from . import misc
from . import broadcast
from . import transmission_format
from . import attachment

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
    encoding = Column(String(63), nullable=False)
    alphabet_id = Column(Integer, ForeignKey(misc.Alphabet.id))
    attribution = Column(String(255))
    contents = Column(Binary, nullable=True)

    transmission = relationship(Transmission, backref=backref("contents"))
    alphabet = relationship(misc.Alphabet)

class TransmissionContentNode(base.Base):
    __tablename__ = "transmission_content_nodes"

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("transmission_content_nodes.id"))
    format_node_id = Column(Integer, ForeignKey(transmission_format.TransmissionFormatNode.id), nullable=False)
    order = Column(Integer, nullable=False)
    segment = Column(Binary, nullable=False)

    children = relationship(
        "TransmissionContentNode",
        backref=backref("parent", remote_side=[id])
    )
    format_node = relationship(transmission_format.TransmissionFormatNode)

class TransmissionStructuredContents(TransmissionContents):
    __tablename__ = "transmission_structured_contents"
    __mapper_args__ = {"polymorphic_identity": "structured_contents"}

    id = Column(Integer, ForeignKey(TransmissionContents.id), primary_key=True)
    root_node_id = Column(Integer, ForeignKey(TransmissionContentNode.id), nullable=False)
    format_id = Column(Integer, ForeignKey(transmission_format.TransmissionFormat.id), nullable=False)

    root_node = relationship(TransmissionContentNode)
    format = relationship(transmission_format.TransmissionFormat)

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
