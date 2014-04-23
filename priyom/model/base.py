# encoding=utf8
from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy import event, Column, DateTime

class Base(declarative_base()):
    __abstract__ = True
    __table_args__ = {
        "mysql_character_set": "utf8",
        "mysql_collate": "utf8_general_ci"
    }

def update_timestamp(mapper, connection, target):
    target.modified = datetime.utcnow()

class TopLevelMeta(DeclarativeMeta):
    def __init__(cls, name, bases, dct):
        DeclarativeMeta.__init__(cls, name, bases, dct)
        if dct.get("__metaclass__", None) is not TopLevelMeta:
            event.listen(cls, "before_update", update_timestamp)

class TopLevel(Base, metaclass=TopLevelMeta):
    """
    TopLevel objects come with :attr:`created` and :attr:`modified` timestamps.
    ``modified`` gets updated automatically when an attribute of the object is
    changed and changes are committed. This is also done even if there is no
    net change in column values.
    """
    __abstract__ = True

    created = Column(DateTime, nullable=False)
    modified = Column(DateTime, nullable=False)

    def __init__(self, *args, **kwargs):
        super(TopLevel, self).__init__(*args, **kwargs)
        self.created = datetime.utcnow()
        self.modified = datetime.utcnow()
