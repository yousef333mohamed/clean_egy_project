"""Daily environmental context."""

from datetime import date
from sqlalchemy import Boolean, Date, Float, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class EnvironmentalDaily(Base):
    """Region-level daily environmental factors."""

    __tablename__ = "environmental_daily"
    __table_args__ = (UniqueConstraint("date", "region"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    region: Mapped[str] = mapped_column(String(120), index=True)
    temperature_c: Mapped[float] = mapped_column(Float)
    rainfall_mm: Mapped[float] = mapped_column(Float)
    is_holiday: Mapped[bool] = mapped_column(Boolean)
    is_festival: Mapped[bool] = mapped_column(Boolean)
    is_weekend: Mapped[bool] = mapped_column(Boolean)
    traffic_level: Mapped[str] = mapped_column(String(40))
