# encoding=utf8
from __future__ import unicode_literals, print_function, absolute_import

from sqlalchemy import *
from sqlalchemy.orm import relationship, backref, validates

from . import base as base

class Attachment(base.Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True)
    mime = Column(String(63), nullable=False)
    filename = Column(String(255), nullable=False)
    attribution = Column(String(127))
