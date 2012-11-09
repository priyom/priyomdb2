# encoding=utf8
from __future__ import absolute_import, print_function, unicode_literals

class Interface(object):
    """
    High-level interface to the priyom db data layer.
    """

    def __init__(self, sql_session):
        self._session = sql_session
