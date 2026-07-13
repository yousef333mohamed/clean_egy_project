"""Smart-bin telemetry model."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.smart_bin import SmartBin


class SmartBinReading(Base):
    """Timestamped telemetry from ``smart_bin_readings.csv``."""

    __tablename__ = "smart_bin_readings"
    __table_args__ = (
        UniqueConstraint("bin_id", "timestamp", name="uq_smart_bin_readings_bin_timestamp"),
        Index("ix_smart_bin_readings_bin_timestamp", "bin_id", "timestamp"),
        CheckConstraint("fill_level_pct BETWEEN 0 AND 100", name="ck_smart_bin_readings_fill_pct"),
        CheckConstraint("humidity_pct BETWEEN 0 AND 100", name="ck_smart_bin_readings_humidity_pct"),
        CheckConstraint("battery_level_pct BETWEEN 0 AND 100", name="ck_smart_bin_readings_battery_pct"),
        CheckConstraint("waste_weight_kg >= 0", name="ck_smart_bin_readings_weight_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bin_id: Mapped[str] = mapped_column(ForeignKey("smart_bins.bin_id", ondelete="CASCADE"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    fill_level_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    waste_weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    waste_type: Mapped[str] = mapped_column(String(60), nullable=False)
    temperature_c: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    humidity_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    battery_level_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    sensor_status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    was_collected: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)

    smart_bin: Mapped["SmartBin"] = relationship(back_populates="readings", lazy="raise")
