"""Truck trip model."""

from datetime import date
from typing import TYPE_CHECKING
from sqlalchemy import Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.truck import Truck


class TruckTrip(Base):
    """Daily collection trip log."""

    __tablename__ = "truck_trip_logs"
    __table_args__ = (UniqueConstraint("truck_id", "date"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    truck_id: Mapped[str] = mapped_column(ForeignKey("trucks.truck_id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    region: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(40))
    distance_km: Mapped[float] = mapped_column(Float)
    fuel_consumed_l: Mapped[float] = mapped_column(Float)
    load_kg: Mapped[float] = mapped_column(Float)
    avg_speed_kmh: Mapped[float] = mapped_column(Float)
    stops_completed: Mapped[int] = mapped_column(Integer)
    trip_duration_min: Mapped[float] = mapped_column(Float)
    truck: Mapped["Truck"] = relationship(back_populates="trips")
