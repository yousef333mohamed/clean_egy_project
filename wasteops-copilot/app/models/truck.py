"""Truck asset model."""

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.truck_trip_log import TruckTripLog


class Truck(Base):
    """Collection truck asset from ``trucks.csv``."""

    __tablename__ = "trucks"
    __table_args__ = (
        CheckConstraint("capacity_kg > 0", name="ck_trucks_capacity_positive"),
        CheckConstraint("model_year BETWEEN 1980 AND 2100", name="ck_trucks_model_year_reasonable"),
    )

    truck_id: Mapped[str] = mapped_column(String(50), primary_key=True, unique=True, index=True)
    region: Mapped[str] = mapped_column(String(120), nullable=False)
    capacity_kg: Mapped[int] = mapped_column(Integer, nullable=False)
    model_year: Mapped[int] = mapped_column(Integer, nullable=False)
    fuel_type: Mapped[str] = mapped_column(String(40), nullable=False)

    trip_logs: Mapped[list["TruckTripLog"]] = relationship(back_populates="truck", cascade="all, delete-orphan", lazy="selectin")
