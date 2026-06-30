from uuid import UUID, uuid4
from datetime import datetime, UTC
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class UserCredential(Base):
    __tablename__ = "user_credentials"
    __table_args__ = (UniqueConstraint("user_id", "platform", name="uq_user_credentials_user_platform"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    platform: Mapped[str]
    credentials_encrypted: Mapped[bytes]
    is_healthy: Mapped[bool] = mapped_column(default=True)
    last_validated_at: Mapped[datetime | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC).replace(tzinfo=None))
