"""scope analysis runs to their authenticated owner

Revision ID: 20260805_0002
Revises: 20260714_0001
Create Date: 2026-08-05
"""

from alembic import op
import sqlalchemy as sa


revision = "20260805_0002"
down_revision = "20260714_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Existing runs have no trustworthy owner. They intentionally remain
    # unassigned and are not exposed through owner-scoped API queries.
    with op.batch_alter_table("analysis_runs") as batch_op:
        batch_op.add_column(sa.Column("owner_user_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_analysis_runs_owner_user_id_users", "users", ["owner_user_id"], ["id"])
        batch_op.create_index("ix_analysis_runs_owner_user_id", ["owner_user_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("analysis_runs") as batch_op:
        batch_op.drop_index("ix_analysis_runs_owner_user_id")
        batch_op.drop_constraint("fk_analysis_runs_owner_user_id_users", type_="foreignkey")
        batch_op.drop_column("owner_user_id")
