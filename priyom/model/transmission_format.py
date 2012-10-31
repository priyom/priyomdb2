# encoding=utf8
from __future__ import unicode_literals, print_function, absolute_import

from sqlalchemy import *
from sqlalchemy import event
from sqlalchemy.orm import relationship, backref, validates

from . import base as base

class TransmissionFormatNode(base.Base):
    __tablename__ = "transmission_format_nodes"

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("transmission_format_nodes.id"))
    order = Column(Integer)
    duplicity = Column(Enum(
        "one",
        "one_or_more",
        "zero_or_more",
        "fixed"
    ), nullable=False)
    count = Column(Integer)
    content_match = Column(String(127))

    children = relationship(
        "TransmissionFormatNode",
        backref=backref("parent", remote_side=[id])
    )

    @validates('count')
    def validate_count(self, key, count):
        if self.duplicity != "fixed":
            if count is not None:
                raise ValueError("Only NULL count is allowed for duplicity != fixed")
        else:
            if count is None:
                raise ValueError("NULL count is not allowed for duplicity == fixed")
        return count

    @validates('children')
    def validate_child(self, key, child):
        assert child.order is not None
        return child

    @validates('parent')
    def validate_parent(self, key, parent):
        assert parent.content_match is None
        return parent


class TransmissionFormat(base.TopLevel):
    __tablename__ = "transmission_formats"

    id = Column(Integer, primary_key=True)
    display_name = Column(String(127), nullable=False)
    description = Column(Text)
    root_node_id = Column(Integer, ForeignKey(TransmissionFormatNode.id))

    root_node = relationship(TransmissionFormatNode)
