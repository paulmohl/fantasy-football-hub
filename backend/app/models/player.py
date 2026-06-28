from datetime import datetime, UTC
from sqlalchemy import Index
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class PlayerCrossMap(Base):
    __tablename__ = "player_cross_map"
    __table_args__ = (
        Index("ix_player_cross_map_yahoo_id", "yahoo_id"),
        Index("ix_player_cross_map_espn_id", "espn_id"),
    )

    sleeper_id: Mapped[str] = mapped_column(primary_key=True)
    yahoo_id: Mapped[str | None] = mapped_column(default=None)
    espn_id: Mapped[str | None] = mapped_column(default=None)
    full_name: Mapped[str]
    position: Mapped[str | None] = mapped_column(default=None)
    team: Mapped[str | None] = mapped_column(default=None)
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC).replace(tzinfo=None))
