"""Smart-bin asset model."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.operational_daily import OperationalDaily
    from app.models.smart_bin_reading import SmartBinReading


class SmartBin(Base):
    """Installed smart-bin asset from ``smart_bins.csv``."""

    __tablename__ = "smart_bins"
    __table_args__ = (CheckConstraint("capacity_liters > 0", name="ck_smart_bins_capacity_positive"),)

    bin_id: Mapped[str] = mapped_column(String(120), primary_key=True, unique=True, index=True)
    governorate: Mapped[str] = mapped_column(String(120), nullable=False)
    region: Mapped[str] = mapped_column(String(120), nullable=False)
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    capacity_liters: Mapped[int] = mapped_column(Integer, nullable=False)
    primary_waste_type: Mapped[str] = mapped_column(String(60), nullable=False)
    install_date: Mapped[date] = mapped_column(Date, nullable=False)

    readings: Mapped[list["SmartBinReading"]] = relationship(back_populates="smart_bin", cascade="all, delete-orphan", lazy="selectin")
    operational_records: Mapped[list["OperationalDaily"]] = relationship(back_populates="smart_bin", cascade="all, delete-orphan", lazy="selectin")
