"""More user attributes

Revision ID: 2b60ac76e3f
Revises: None
Create Date: 2014-09-18 13:18:04.908395

"""

# revision identifiers, used by Alembic.
revision = '2b60ac76e3f'
down_revision = None

from sqlalchemy import *
from alembic import op
import sqlalchemy.sql as sql

def upgrade():
    op.add_column(
        "users",
        Column("timezone",
               Unicode(length=127),
               nullable=False,
               server_default="Etc/UTC"))
    op.add_column(
        "users",
        Column("locale",
               Unicode(length=31),
               nullable=False,
               server_default="en_GB"))


def downgrade():
    op.drop_column(
        "users",
        "locale")
    op.drop_column(
        "users",
        "timezone")
