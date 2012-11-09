# encoding=utf8
from __future__ import absolute_import, print_function, unicode_literals

import priyom.model as model

def check_consistency(session):
    """
    Run a partial consistency check on the database. Raises appropriate
    exceptions if inconsistencies are detected.

    This only checks relationships and data values which are not covered by
    validation or database-level constraints.
    """


