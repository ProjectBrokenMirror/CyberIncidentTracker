from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="success")
    total_raw: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_normalized: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_deduped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_persisted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_unmatched: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_skipped_duplicates: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_organizations_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
