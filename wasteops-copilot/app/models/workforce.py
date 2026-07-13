"""Workforce model."""

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.attendance import Attendance


class Worker(Base):
    """Waste-operations worker."""

    __tablename__ = "workforce"
    worker_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    governorate: Mapped[str] = mapped_column(String(120))
    region: Mapped[str] = mapped_column(String(120), index=True)
    shift: Mapped[str] = mapped_column(String(40))
    experience_years: Mapped[int] = mapped_column(Integer)
    attendance: Mapped[list["Attendance"]] = relationship(back_populates="worker", cascade="all, delete-orphan")
