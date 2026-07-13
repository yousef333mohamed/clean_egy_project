"""Workforce model."""

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.workforce_attendance import WorkforceAttendance


class Worker(Base):
    """Waste-operations worker from ``workforce.csv``."""

    __tablename__ = "workers"
    __table_args__ = (CheckConstraint("experience_years >= 0", name="ck_workers_experience_nonnegative"),)

    worker_id: Mapped[str] = mapped_column(String(120), primary_key=True, unique=True, index=True)
    governorate: Mapped[str] = mapped_column(String(120), nullable=False)
    region: Mapped[str] = mapped_column(String(120), nullable=False)
    shift: Mapped[str] = mapped_column(String(40), nullable=False)
    experience_years: Mapped[int] = mapped_column(Integer, nullable=False)

    attendance_records: Mapped[list["WorkforceAttendance"]] = relationship(back_populates="worker", cascade="all, delete-orphan", lazy="selectin")
