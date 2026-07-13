"""Truck trip-log model."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.truck import Truck


class TruckTripLog(Base):
    """Daily collection trip from ``truck_trip_logs.csv``."""

    __tablename__ = "truck_trip_logs"
    __table_args__ = (
        UniqueConstraint("truck_id", "date", name="uq_truck_trip_logs_truck_date"),
        CheckConstraint("distance_km >= 0", name="ck_truck_trip_logs_distance_nonnegative"),
        CheckConstraint("fuel_consumed_l >= 0", name="ck_truck_trip_logs_fuel_nonnegative"),
        CheckConstraint("load_kg >= 0", name="ck_truck_trip_logs_load_nonnegative"),
        CheckConstraint("avg_speed_kmh >= 0", name="ck_truck_trip_logs_speed_nonnegative"),
        CheckConstraint("stops_completed >= 0", name="ck_truck_trip_logs_stops_nonnegative"),
        CheckConstraint("trip_duration_min >= 0", name="ck_truck_trip_logs_duration_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    truck_id: Mapped[str] = mapped_column(ForeignKey("trucks.truck_id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    region: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    distance_km: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fuel_consumed_l: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    load_kg: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    avg_speed_kmh: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    stops_completed: Mapped[int] = mapped_column(Integer, nullable=False)
    trip_duration_min: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    truck: Mapped["Truck"] = relationship(back_populates="trip_logs", lazy="raise")
