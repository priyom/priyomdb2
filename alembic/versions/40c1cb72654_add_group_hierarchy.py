"""add group hierarchy

Revision ID: 40c1cb72654
Revises: db89bb165d
Create Date: 2014-10-10 15:48:09.406326

"""

# revision identifiers, used by Alembic.
revision = '40c1cb72654'
down_revision = 'db89bb165d'

from sqlalchemy import *
from alembic import op
import sqlalchemy.sql as sql


def upgrade():
    op.add_column(
        "groups",
        Column(
            "supergroup_id",
            Integer,
            ForeignKey("groups.id",
                       name="groups_fk_supergroup_id",
                       ondelete="SET NULL"),
            nullable=True))

def downgrade():
    op.drop_constraint(
        "groups_fk_supergroup_id",
        "groups",
        type_="foreignkey")
    op.drop_column(
        "groups",
        "supergroup_id")
