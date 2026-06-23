"""phase1_auth_league

Revision ID: 001_phase1_auth_league
Revises:
Create Date: 2026-06-23 16:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_phase1_auth_league"
depends_on: Union[Sequence[str], None] = None
down_revision: Union[str, None] = None
branch_labels: Union[Sequence[str], None] = None


def upgrade() -> None:
    # users table
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=True),
        sa.Column("google_sub", sa.String(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("envelope_key", sa.LargeBinary(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("google_sub"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # sessions table
    op.create_table(
        "sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )

    # leagues table
    op.create_table(
        "leagues",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("host_platform", sa.String(), nullable=False),
        sa.Column("host_league_id", sa.String(), nullable=False),
        sa.Column("season", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("scoring_rules", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("roster_format", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("draft_type", sa.String(), nullable=True),
        sa.Column("keeper_flag", sa.Boolean(), nullable=False),
        sa.Column("dynasty_flag", sa.Boolean(), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("host_platform", "host_league_id", "season"),
    )

    # league_members table
    op.create_table(
        "league_members",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("league_id", sa.UUID(), nullable=False),
        sa.Column("host_team_id", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["league_id"], ["leagues.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "league_id"),
    )

    # teams table
    op.create_table(
        "teams",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("league_id", sa.UUID(), nullable=False),
        sa.Column("host_team_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("owner_user_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["league_id"], ["leagues.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("league_id", "host_team_id"),
    )

    # rosters table
    op.create_table(
        "rosters",
        sa.Column("team_id", sa.UUID(), nullable=False),
        sa.Column("week", sa.Integer(), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("team_id", "week"),
    )

    # audit_log table
    op.create_table(
        "audit_log",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("target_type", sa.String(), nullable=True),
        sa.Column("target_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("rosters")
    op.drop_table("teams")
    op.drop_table("league_members")
    op.drop_table("leagues")
    op.drop_table("sessions")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
