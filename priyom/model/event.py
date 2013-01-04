# encoding=utf8
from __future__ import unicode_literals, print_function, absolute_import

from sqlalchemy import *
from sqlalchemy.orm import relationship, backref

from . import base as base
from . import misc as misc
from . import station as station

class EventClass(base.TopLevel):
    __tablename__ = 'event_classes'

    id = Column(Integer, primary_key=True)
    display_name = Column(String(127), nullable=False)
    one_shot = Column(Boolean, default=True, nullable=False)

class Event(base.TopLevel):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    station_id = Column(Integer, ForeignKey(station.Station.id))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    event_class_id = Column(Integer, ForeignKey(EventClass.id))

    station = relationship(station.Station, backref=backref("events"), order_by=start_time)
    event_class = relationship(EventClass)
