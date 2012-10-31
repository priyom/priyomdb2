#!/usr/bin/python2
# encoding=utf8
from __future__ import absolute_import, unicode_literals, print_function

import time
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import priyom.model as model

engine = create_engine('mysql://priyom2@localhost/priyom2', echo=False)

model.Base.metadata.create_all(engine)
session = sessionmaker(bind=engine)()

station = model.Station("S28", None)
session.add(station)
session.commit()
time.sleep(2)
station.nickname = "foobar"
session.commit()

try:
    assert station.created != station.modified
finally:
    session.delete(station)
    session.commit()

tx = model.Transmission()
tx.timestamp = datetime.utcnow()
tx.duration = 100
attachment = model.TransmissionAttachment()
attachment.transmission = tx
attachment.filename = "foo/bar"
attachment.mime = "text/plain"
attachment.relation = "waterfall"
attachment.attribution = "by Avare"
session.add(tx)
session.add(attachment)
session.commit()
try:
    time.sleep(10)
finally:
    session.delete(attachment)
    session.commit()
