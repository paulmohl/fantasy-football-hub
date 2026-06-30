"""phase3_credentials_playermap

Revision ID: 002_phase3_credentials_playermap
Revises: 001_phase1_auth_league
Create Date: 2026-06-28 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_phase3_credentials_playermap"
down_revision: Union[str, None] = "001_phase1_auth_league"
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_credentials",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("credentials_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column("is_healthy", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_validated_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "platform", name="uq_user_credentials_user_platform"),
    )

    op.create_table(
        "player_cross_map",
        sa.Column("sleeper_id", sa.String(), nullable=False),
        sa.Column("yahoo_id", sa.String(), nullable=True),
        sa.Column("espn_id", sa.String(), nullable=True),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("position", sa.String(), nullable=True),
        sa.Column("team", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("sleeper_id"),
    )
    op.create_index("ix_player_cross_map_yahoo_id", "player_cross_map", ["yahoo_id"])
    op.create_index("ix_player_cross_map_espn_id", "player_cross_map", ["espn_id"])


def downgrade() -> None:
    op.drop_index("ix_player_cross_map_espn_id", table_name="player_cross_map")
    op.drop_index("ix_player_cross_map_yahoo_id", table_name="player_cross_map")
    op.drop_table("player_cross_map")
    op.drop_table("user_credentials")
