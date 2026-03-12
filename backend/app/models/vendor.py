from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Vendor(Base):
    __tablename__ = "vendors"
    __table_args__ = (UniqueConstraint("tenant_id", "organization_id", name="uq_vendors_tenant_org"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, default="default")
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    criticality: Mapped[str] = mapped_column(String(50), default="medium")
