from uuid import UUID, uuid4
from datetime import datetime, UTC
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class League(Base):
    __tablename__ = "leagues"
    __table_args__ = (
        UniqueConstraint("host_platform", "host_league_id", "season"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    host_platform: Mapped[str]
    host_league_id: Mapped[str]
    season: Mapped[str]
    name: Mapped[str]
    scoring_rules: Mapped[dict] = mapped_column(JSONB)
    roster_format: Mapped[dict] = mapped_column(JSONB)
    draft_type: Mapped[str | None] = mapped_column(default=None)
    keeper_flag: Mapped[bool] = mapped_column(default=False)
    dynasty_flag: Mapped[bool] = mapped_column(default=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(default=None)


class LeagueMember(Base):
    __tablename__ = "league_members"
    __table_args__ = (UniqueConstraint("user_id", "league_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    league_id: Mapped[UUID] = mapped_column(ForeignKey("leagues.id", ondelete="CASCADE"))
    host_team_id: Mapped[str | None] = mapped_column(default=None)
    role: Mapped[str] = mapped_column(default="owner")
    connected_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC).replace(tzinfo=None))


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (UniqueConstraint("league_id", "host_team_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    league_id: Mapped[UUID] = mapped_column(ForeignKey("leagues.id", ondelete="CASCADE"))
    host_team_id: Mapped[str]
    name: Mapped[str | None] = mapped_column(default=None)
    owner_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id"), default=None
    )


class Roster(Base):
    __tablename__ = "rosters"

    team_id: Mapped[UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True
    )
    week: Mapped[int] = mapped_column(primary_key=True)
    snapshot: Mapped[dict] = mapped_column(JSONB)
    last_synced_at: Mapped[datetime | None] = mapped_column(default=None)
