# encoding=utf8
from __future__ import unicode_literals, print_function, absolute_import

from sqlalchemy import *
from sqlalchemy.orm import relationship, backref

from .base import Base, TopLevel
from .station import Station

class Modulation(Base):
    __tablename__ = 'modulations'
    __table_args__ = (
        UniqueConstraint('display_name'),
    )

    id = Column(Integer, primary_key=True)
    display_name = Column(String(63), nullable=False)

    def __init__(self, display_name):
        super(Modulation, self).__init__()
        self.display_name = display_name

class EventClass(TopLevel):
    __tablename__ = 'event_classes'

    id = Column(Integer, primary_key=True)
    display_name = Column(String(127), nullable=False)
    one_shot = Column(Boolean, default=True, nullable=False)

class Event(TopLevel):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    station_id = Column(Integer, ForeignKey(Station.id))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    event_class_id = Column(Integer, ForeignKey(EventClass.id))
    approved = Column(Boolean, default=False, nullable=False)

    station = relationship(Station,
                           backref=backref("events"),
                           order_by=start_time)
    event_class = relationship(EventClass)
    frequencies = relationship("EventFrequency",
                               order_by="EventFrequency.frequency")


class EventFrequency(Base):
    __tablename__ = 'event_frequencies'

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey(Event.id), nullable=False)
    frequency = Column(BigInteger, nullable=False)
    modulation_id = Column(Integer, ForeignKey(Modulation.id), nullable=False)

    modulation = relationship(Modulation)
