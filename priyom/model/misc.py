# encoding=utf8
from __future__ import unicode_literals, print_function, absolute_import

from sqlalchemy import *

from . import base as base

class Alphabet(base.Base):
    __tablename__ = 'alphabets'
    __table_args__ = (
        UniqueConstraint('display_name'),
    )

    id = Column(Integer, primary_key=True)
    display_name = Column(String(63), nullable=False)

    def __init__(self, display_name):
        super(Alphabet, self).__init__()
        self.display_name = display_name

class Modulation(base.Base):
    __tablename__ = 'modulations'
    __table_args__ = (
        UniqueConstraint('display_name'),
    )

    id = Column(Integer, primary_key=True)
    display_name = Column(String(63), nullable=False)

    def __init__(self, display_name):
        super(Modulation, self).__init__()
        self.display_name = display_name
