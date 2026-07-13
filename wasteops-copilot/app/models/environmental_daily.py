"""Daily environmental context model."""

from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class EnvironmentalDaily(Base):
    """Region-level environmental record from ``environmental_daily.csv``."""

    __tablename__ = "environmental_daily"
    __table_args__ = (
        UniqueConstraint("date", "region", name="uq_environmental_daily_date_region"),
        CheckConstraint("rainfall_mm >= 0", name="ck_environmental_daily_rainfall_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    region: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    temperature_c: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    rainfall_mm: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_holiday: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_festival: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_weekend: Mapped[bool] = mapped_column(Boolean, nullable=False)
    traffic_level: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
