"""phase4_draft_models

Revision ID: 003_phase4_draft_models
Revises: 002_phase3_credentials_playermap
Create Date: 2026-07-02 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_phase4_draft_models"
down_revision: Union[str, None] = "002_phase3_credentials_playermap"
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "drafts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("league_id", sa.UUID(), nullable=False),
        sa.Column("commissioner_user_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
        sa.Column("timezone", sa.String(), nullable=False, server_default="America/New_York"),
        sa.Column("pick_clock_seconds", sa.Integer(), nullable=False, server_default="90"),
        sa.Column("num_rounds", sa.Integer(), nullable=False, server_default="15"),
        sa.Column("num_teams", sa.Integer(), nullable=False, server_default="12"),
        sa.Column("current_pick_num", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pick_deadline_epoch", sa.Float(), nullable=True),
        sa.Column("draft_order", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["commissioner_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["league_id"], ["leagues.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "draft_picks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("draft_id", sa.UUID(), nullable=False),
        sa.Column("pick_num", sa.Integer(), nullable=False),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.UUID(), nullable=False),
        sa.Column("player_id", sa.String(), nullable=False),
        sa.Column("is_auto_pick", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("picked_at", sa.DateTime(), nullable=False),
        sa.Column("reactions", sa.JSON(), nullable=False, server_default="{}"),
        sa.ForeignKeyConstraint(["draft_id"], ["drafts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("draft_id", "pick_num", name="uq_draft_picks_draft_pick_num"),
        sa.UniqueConstraint("draft_id", "player_id", name="uq_draft_picks_draft_player"),
    )
    op.create_index("ix_draft_picks_draft_id_pick_num", "draft_picks", ["draft_id", "pick_num"])
    op.create_index("ix_draft_picks_draft_id_player_id", "draft_picks", ["draft_id", "player_id"])

    op.create_table(
        "draft_queue",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("draft_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("player_id", sa.String(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["draft_id"], ["drafts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("draft_id", "user_id", "player_id", name="uq_draft_queue_draft_user_player"),
    )
    op.create_index("ix_draft_queue_draft_user_position", "draft_queue", ["draft_id", "user_id", "position"])

    op.create_table(
        "draft_chat_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("draft_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["draft_id"], ["drafts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_draft_chat_messages_draft_created", "draft_chat_messages", ["draft_id", "created_at"])

    op.create_table(
        "user_draft_rankings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("draft_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("player_id", sa.String(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(), nullable=False, server_default="fantasycalc"),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["draft_id"], ["drafts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("draft_id", "user_id", "player_id", name="uq_user_draft_rankings_draft_user_player"),
    )
    op.create_index("ix_user_draft_rankings_draft_user_rank", "user_draft_rankings", ["draft_id", "user_id", "rank"])


def downgrade() -> None:
    op.drop_index("ix_user_draft_rankings_draft_user_rank", table_name="user_draft_rankings")
    op.drop_table("user_draft_rankings")
    op.drop_index("ix_draft_chat_messages_draft_created", table_name="draft_chat_messages")
    op.drop_table("draft_chat_messages")
    op.drop_index("ix_draft_queue_draft_user_position", table_name="draft_queue")
    op.drop_table("draft_queue")
    op.drop_index("ix_draft_picks_draft_id_player_id", table_name="draft_picks")
    op.drop_index("ix_draft_picks_draft_id_pick_num", table_name="draft_picks")
    op.drop_table("draft_picks")
    op.drop_table("drafts")
