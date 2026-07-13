"""Attendance model."""

from datetime import date
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.workforce import Worker


class Attendance(Base):
    """Daily worker attendance and performance."""

    __tablename__ = "workforce_attendance"
    __table_args__ = (UniqueConstraint("worker_id", "date"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    worker_id: Mapped[str] = mapped_column(ForeignKey("workforce.worker_id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    present: Mapped[bool] = mapped_column(Boolean)
    completed_tasks: Mapped[int] = mapped_column(Integer)
    overtime_hours: Mapped[float] = mapped_column(Float)
    performance_score: Mapped[float] = mapped_column(Float)
    worker: Mapped["Worker"] = relationship(back_populates="attendance")
