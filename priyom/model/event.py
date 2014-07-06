# encoding=utf8
from __future__ import unicode_literals, print_function, absolute_import

import math

from sqlalchemy import *
from sqlalchemy.orm import relationship, backref

from .base import Base, TopLevel
from .station import Station
from .user import User

def pretty_print_frequency(freq):
    if freq == 0:
        order_of_magnitude = 0
    else:
        order_of_magnitude = int(math.log10(freq))
    prefix = int(order_of_magnitude / 3)
    if prefix > 3:
        prefix = 3
    def lossless(x, prefix):
        divisor = 10**((prefix-1)*3)
        y = int(x / divisor) * divisor
        return x == y
    while not lossless(freq, prefix) and prefix > 0:
        prefix -= 1
    prefix_char = ["", "k", "M", "G"][prefix]
    return "{:.3f} {}Hz".format(
        freq / 10**(prefix*3),
        prefix_char)

class Mode(Base):
    __tablename__ = 'modes'
    __table_args__ = (
        UniqueConstraint('display_name'),
    )

    id = Column(Integer, primary_key=True)
    display_name = Column(String(63), nullable=False)

    def __init__(self, display_name):
        super(Mode, self).__init__()
        self.display_name = display_name

    def __str__(self):
        return self.display_name

class EventClass(TopLevel):
    __tablename__ = 'event_classes'

    id = Column(Integer, primary_key=True)
    display_name = Column(String(127), nullable=False)
    one_shot = Column(Boolean, default=True, nullable=False)

    def __str__(self):
        return self.display_name

class Event(TopLevel):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    station_id = Column(Integer, ForeignKey(Station.id))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    event_class_id = Column(Integer, ForeignKey(EventClass.id))
    submitter_id = Column(Integer, ForeignKey(User.id))
    approved = Column(Boolean, default=False, nullable=False)

    station = relationship(Station,
                           backref=backref("events"),
                           order_by=start_time)
    event_class = relationship(EventClass)
    frequencies = relationship("EventFrequency",
                               backref=backref("event"),
                               order_by="EventFrequency.frequency",
                               cascade="all, delete-orphan",
                               passive_deletes=True)
    submitter = relationship(User,
                             backref=backref("submitted_events"))

    def __str__(self):
        if self.event_class is None:
            return "Transmission event (Station {!s}) at {}".format(
                self.station if self.station else "??",
                self.start_time)
        else:
            return "{!s} event (Station {!s}) at {}".format(
                self.event_class,
                self.station if self.station else "??",
                self.start_time)


class EventFrequency(Base):
    __tablename__ = 'event_frequencies'

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer,
                      ForeignKey(Event.id,
                                 ondelete="CASCADE"),
                      nullable=False)
    frequency = Column(BigInteger, nullable=False)
    mode_id = Column(Integer, ForeignKey(Mode.id), nullable=False)

    mode = relationship(Mode)

    def __str__(self):
        return "{} ({})".format(
            pretty_print_frequency(self.frequency),
            self.mode)
