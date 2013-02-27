#!/usr/bin/python2
# encoding=utf8
from __future__ import absolute_import, unicode_literals, print_function

import time
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import priyom.consistency
import priyom.model as model

engine = create_engine('mysql://priyom2@localhost/priyom2', echo=False)

model.Base.metadata.create_all(engine)
session = sessionmaker(bind=engine)()

priyom.consistency.check_consistency(session)
