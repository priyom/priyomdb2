"""add timestamps for users

Revision ID: db89bb165d
Revises: 2b60ac76e3f
Create Date: 2014-09-26 14:57:31.746853

"""

# revision identifiers, used by Alembic.
revision = 'db89bb165d'
down_revision = '2b60ac76e3f'

from sqlalchemy import *
from alembic import op
import sqlalchemy.sql as sql


def upgrade():
    op.add_column(
        "users",
        Column("created", DateTime, nullable=False)
    )
    op.add_column(
        "users",
        Column("modified", DateTime, nullable=False)
    )

    # set all rows to a sensible value
    users = sql.table(
        "users",
        sql.column("created"),
        sql.column("modified"),
    )

    op.execute(
        users.update().values(
            created=text("NOW()"),
            modified=text("NOW()"),
        )
    )

def downgrade():
    op.drop_column("users", "created")
    op.drop_column("users", "modified")
