# encoding=utf8
from __future__ import unicode_literals, print_function, absolute_import

from sqlalchemy import *
from sqlalchemy.orm import relationship, backref

from . import base as base
from . import misc as misc
from . import station as station

class Broadcast(base.TopLevel):
    __tablename__ = 'broadcasts'

    id = Column(Integer, primary_key=True)
    station_id = Column(Integer, ForeignKey(station.Station.id))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    kind = Column(Enum(
        "transmission",
        "marker",
        "other / unknown"
    ))

    station = relationship(station.Station, backref=backref("broadcasts"), order_by=start_time)
    frequencies = relationship("BroadcastFrequency", order_by="BroadcastFrequency.frequency")

class BroadcastFrequency(base.Base):
    __tablename__ = 'broadcast_frequencies'
    id = Column(Integer, primary_key=True)
    broadcast_id = Column(Integer, ForeignKey(Broadcast.id), nullable=False)
    frequency = Column(BigInteger, nullable=False)
    modulation_id = Column(Integer, ForeignKey(misc.Modulation.id), nullable=False)

    modulation = relationship(misc.Modulation)

