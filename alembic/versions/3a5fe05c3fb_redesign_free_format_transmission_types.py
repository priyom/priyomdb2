"""redesign free format transmission types

Revision ID: 3a5fe05c3fb
Revises: 40c1cb72654
Create Date: 2014-11-07 17:50:30.548990

"""

# revision identifiers, used by Alembic.
revision = '3a5fe05c3fb'
down_revision = '40c1cb72654'

from sqlalchemy import *
from alembic import op
import sqlalchemy.sql as sql

import priyom.model

def upgrade():
    op.drop_column(
        "transmission_raw_contents",
        "encoding")
    op.create_table(
        "transmission_freetext_contents",
        Column("id",
               Integer,
               ForeignKey(priyom.model.Contents.id,
                          ondelete="CASCADE"),
               primary_key=True),
        Column("contents", Text, nullable=True)
    )


def downgrade():
    op.drop_table("transmission_freetext_contents")
    op.add_column(
        "transmission_raw_contents",
        Column("encoding", Unicode(50), server_default="binary", nullable=False)
    )
