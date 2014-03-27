# encoding=utf8
from __future__ import unicode_literals, print_function, absolute_import

from sqlalchemy import *

from . import base as base

class Station(base.TopLevel):
    __tablename__ = 'stations'
    __table_args__ = (
        UniqueConstraint("enigma_id", "priyom_id"),
    )

    id = Column(Integer, primary_key=True)

    # at least InnoDB won't enforce uniqueness over nullable columns
    enigma_id = Column(Unicode(23), nullable=False)
    priyom_id = Column(Unicode(23), nullable=False)

    nickname = Column(Unicode(127))
    description = Column(UnicodeText)
    status = Column(Unicode(255))
    location = Column(Unicode(255))

    def __init__(self, enigma_id, priyom_id):
        if not enigma_id and not priyom_id:
            raise ValueError("Station must be provided with at least one of the"
                             " identifiers, priyom_id or enigma_id.")
        super(Station, self).__init__()
        self.enigma_id = enigma_id or ""
        self.priyom_id = priyom_id or ""

    def __str__(self):
        nickname = " ({})".format(self.nickname) if self.nickname else ""
        if self.enigma_id:
            pid = " / {}".format(self.priyom_id) if self.priyom_id else ""
            return "{}{}{}".format(self.enigma_id, pid, nickname)
        else:
            pid = "{}".format(self.priyom_id) if self.priyom_id else \
                  "No ID assigned (#{})".format(self.id)
            return "{}{}".format(pid, nickname)
