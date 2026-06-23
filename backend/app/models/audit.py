from uuid import UUID, uuid4
from datetime import datetime, UTC
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    action: Mapped[str]
    target_type: Mapped[str | None] = mapped_column(default=None)
    target_id: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, default=None)
