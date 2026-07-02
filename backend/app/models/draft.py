from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Draft(Base):
    __tablename__ = "drafts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    league_id: Mapped[UUID] = mapped_column(ForeignKey("leagues.id", ondelete="CASCADE"))
    commissioner_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(default="pending")  # pending|live|paused|complete
    scheduled_at: Mapped[datetime | None] = mapped_column(default=None)
    timezone: Mapped[str] = mapped_column(default="America/New_York")
    pick_clock_seconds: Mapped[int] = mapped_column(default=90)
    num_rounds: Mapped[int] = mapped_column(default=15)
    num_teams: Mapped[int] = mapped_column(default=12)
    current_pick_num: Mapped[int] = mapped_column(default=0)
    pick_deadline_epoch: Mapped[float | None] = mapped_column(default=None)
    draft_order: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC).replace(tzinfo=None)
    )


class DraftPick(Base):
    __tablename__ = "draft_picks"
    __table_args__ = (
        UniqueConstraint("draft_id", "pick_num", name="uq_draft_picks_draft_pick_num"),
        UniqueConstraint("draft_id", "player_id", name="uq_draft_picks_draft_player"),
        Index("ix_draft_picks_draft_id_pick_num", "draft_id", "pick_num"),
        Index("ix_draft_picks_draft_id_player_id", "draft_id", "player_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    draft_id: Mapped[UUID] = mapped_column(ForeignKey("drafts.id", ondelete="CASCADE"))
    pick_num: Mapped[int]
    round: Mapped[int]
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"))
    player_id: Mapped[str]
    is_auto_pick: Mapped[bool] = mapped_column(default=False)
    picked_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC).replace(tzinfo=None)
    )
    reactions: Mapped[dict] = mapped_column(JSONB, default=dict)


class DraftQueue(Base):
    __tablename__ = "draft_queue"
    __table_args__ = (
        UniqueConstraint("draft_id", "user_id", "player_id", name="uq_draft_queue_draft_user_player"),
        Index("ix_draft_queue_draft_user_position", "draft_id", "user_id", "position"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    draft_id: Mapped[UUID] = mapped_column(ForeignKey("drafts.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    player_id: Mapped[str]
    position: Mapped[int]
    added_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC).replace(tzinfo=None)
    )


class DraftChatMessage(Base):
    __tablename__ = "draft_chat_messages"
    __table_args__ = (
        Index("ix_draft_chat_messages_draft_created", "draft_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    draft_id: Mapped[UUID] = mapped_column(ForeignKey("drafts.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    message: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC).replace(tzinfo=None)
    )


class UserDraftRanking(Base):
    __tablename__ = "user_draft_rankings"
    __table_args__ = (
        UniqueConstraint("draft_id", "user_id", "player_id", name="uq_user_draft_rankings_draft_user_player"),
        Index("ix_user_draft_rankings_draft_user_rank", "draft_id", "user_id", "rank"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    draft_id: Mapped[UUID] = mapped_column(ForeignKey("drafts.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    player_id: Mapped[str]
    rank: Mapped[int]
    source: Mapped[str] = mapped_column(default="fantasycalc")  # fantasycalc|csv|manual
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC).replace(tzinfo=None)
    )
