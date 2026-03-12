from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class VendorWatcher(Base):
    __tablename__ = "vendor_watchers"
    __table_args__ = (UniqueConstraint("vendor_id", "email", name="uq_vendor_watchers_vendor_email"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, default="default")
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), index=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
