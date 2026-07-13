"""Workforce attendance model."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.worker import Worker


class WorkforceAttendance(Base):
    """Daily attendance from ``workforce_attendance.csv``.

    The inspected source contains 10,170 scores spanning exactly 0 through 100,
    supporting the percentage-style database constraint below.
    """

    __tablename__ = "workforce_attendance"
    __table_args__ = (
        UniqueConstraint("worker_id", "date", name="uq_workforce_attendance_worker_date"),
        CheckConstraint("completed_tasks >= 0", name="ck_workforce_attendance_tasks_nonnegative"),
        CheckConstraint("overtime_hours >= 0", name="ck_workforce_attendance_overtime_nonnegative"),
        CheckConstraint("performance_score BETWEEN 0 AND 100", name="ck_workforce_attendance_performance_score"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    worker_id: Mapped[str] = mapped_column(ForeignKey("workers.worker_id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    present: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    completed_tasks: Mapped[int] = mapped_column(Integer, nullable=False)
    overtime_hours: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    performance_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    worker: Mapped["Worker"] = relationship(back_populates="attendance_records", lazy="raise")
