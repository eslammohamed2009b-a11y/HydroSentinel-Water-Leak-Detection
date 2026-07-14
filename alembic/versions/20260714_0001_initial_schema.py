"""initial schema

Revision ID: 20260714_0001
Revises: None
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "20260714_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_refresh_tokens_token", "refresh_tokens", ["token"], unique=True)

    op.create_table(
        "scenarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("occupancy_mode", sa.String(length=64), nullable=False),
        sa.Column("expected_has_leak", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_scenarios_slug", "scenarios", ["slug"], unique=True)
    op.create_index("ix_scenarios_file_name", "scenarios", ["file_name"], unique=True)

    op.create_table(
        "scenario_rows",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scenario_id", sa.Integer(), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("row_index", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.String(length=120), nullable=False),
        sa.Column("flow_rate_lpm", sa.Float(), nullable=False),
        sa.Column("avg_pressure_psi", sa.Float(), nullable=False),
        sa.Column("occupancy_status", sa.String(length=64), nullable=False),
    )
    op.create_index("ix_scenario_rows_scenario_id", "scenario_rows", ["scenario_id"], unique=False)

    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("analysis_id", sa.String(length=64), nullable=False),
        sa.Column("scenario_selected", sa.String(length=255), nullable=False),
        sa.Column("event_mode", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_leak", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("leak_lpm", sa.Float(), nullable=False),
        sa.Column("total_liters", sa.Float(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_analysis_runs_analysis_id", "analysis_runs", ["analysis_id"], unique=True)

    op.create_table(
        "analysis_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("analysis_run_id", sa.Integer(), sa.ForeignKey("analysis_runs.id"), nullable=True),
        sa.Column("analysis_id", sa.String(length=64), nullable=False),
        sa.Column("feedback", sa.String(length=120), nullable=False),
        sa.Column("predicted_leak", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("top_timestamp", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_analysis_feedback_analysis_id", "analysis_feedback", ["analysis_id"], unique=False)

    op.create_table(
        "monitor_checks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ok", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("endpoint", sa.String(length=64), nullable=True),
        sa.Column("checked_url", sa.String(length=500), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("message", sa.String(length=1000), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("monitor_checks")
    op.drop_index("ix_analysis_feedback_analysis_id", table_name="analysis_feedback")
    op.drop_table("analysis_feedback")
    op.drop_index("ix_analysis_runs_analysis_id", table_name="analysis_runs")
    op.drop_table("analysis_runs")
    op.drop_index("ix_scenario_rows_scenario_id", table_name="scenario_rows")
    op.drop_table("scenario_rows")
    op.drop_index("ix_scenarios_file_name", table_name="scenarios")
    op.drop_index("ix_scenarios_slug", table_name="scenarios")
    op.drop_table("scenarios")
    op.drop_index("ix_refresh_tokens_token", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")