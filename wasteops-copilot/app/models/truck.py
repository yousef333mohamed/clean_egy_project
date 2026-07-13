"""Truck asset model."""

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.trip import TruckTrip


class Truck(Base):
    """Collection truck master record."""

    __tablename__ = "trucks"
    truck_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    region: Mapped[str] = mapped_column(String(120), index=True)
    capacity_kg: Mapped[int] = mapped_column(Integer)
    model_year: Mapped[int] = mapped_column(Integer)
    fuel_type: Mapped[str] = mapped_column(String(40))
    trips: Mapped[list["TruckTrip"]] = relationship(back_populates="truck", cascade="all, delete-orphan")
