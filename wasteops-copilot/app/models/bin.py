"""Smart-bin models."""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class SmartBin(Base):
    """Installed smart-bin asset."""

    __tablename__ = "smart_bins"
    bin_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    governorate: Mapped[str] = mapped_column(String(120))
    region: Mapped[str] = mapped_column(String(120), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    capacity_liters: Mapped[int] = mapped_column(Integer)
    primary_waste_type: Mapped[str] = mapped_column(String(60))
    install_date: Mapped[date] = mapped_column(Date)
    readings: Mapped[list["SmartBinReading"]] = relationship(back_populates="smart_bin", cascade="all, delete-orphan")


class SmartBinReading(Base):
    """Timestamped smart-bin telemetry."""

    __tablename__ = "smart_bin_readings"
    __table_args__ = (UniqueConstraint("bin_id", "timestamp"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bin_id: Mapped[str] = mapped_column(ForeignKey("smart_bins.bin_id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    fill_level_pct: Mapped[float] = mapped_column(Float)
    waste_weight_kg: Mapped[float] = mapped_column(Float)
    waste_type: Mapped[str] = mapped_column(String(60))
    temperature_c: Mapped[float] = mapped_column(Float)
    humidity_pct: Mapped[float] = mapped_column(Float)
    battery_level_pct: Mapped[float] = mapped_column(Float)
    sensor_status: Mapped[str] = mapped_column(String(40))
    was_collected: Mapped[bool] = mapped_column(Boolean)
    smart_bin: Mapped[SmartBin] = relationship(back_populates="readings")
