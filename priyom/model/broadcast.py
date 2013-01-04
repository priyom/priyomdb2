# encoding=utf8
from __future__ import unicode_literals, print_function, absolute_import

from sqlalchemy import *
from sqlalchemy.orm import relationship, backref

from . import base as base
from . import misc as misc
from . import station as station
from . import event as event

class Broadcast(event.Event):
    __tablename__ = 'broadcasts'
    __mapper_args__ = {"polymorphic_identity": "broadcast_event"}

    id = Column(Integer, ForeignKey(event.Event.id), primary_key=True)
    kind = Column(Enum(
        "transmission",
        "marker",
        "other / unknown"
    ))

    frequencies = relationship("BroadcastFrequency", order_by="BroadcastFrequency.frequency")

class BroadcastFrequency(base.Base):
    __tablename__ = 'broadcast_frequencies'
    id = Column(Integer, primary_key=True)
    broadcast_id = Column(Integer, ForeignKey(Broadcast.id), nullable=False)
    frequency = Column(BigInteger, nullable=False)
    modulation_id = Column(Integer, ForeignKey(misc.Modulation.id), nullable=False)

    modulation = relationship(misc.Modulation)

