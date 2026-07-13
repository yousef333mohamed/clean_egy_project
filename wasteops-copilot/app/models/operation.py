"""Daily operational record."""

from datetime import date
from sqlalchemy import Boolean, Date, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class OperationalDaily(Base):
    """Daily bin-level service outcome."""

    __tablename__ = "operational_daily"
    __table_args__ = (UniqueConstraint("bin_id", "date"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    bin_id: Mapped[str] = mapped_column(ForeignKey("smart_bins.bin_id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    governorate: Mapped[str] = mapped_column(String(120))
    region: Mapped[str] = mapped_column(String(120))
    missed_collection: Mapped[bool] = mapped_column(Boolean)
    emergency_request: Mapped[bool] = mapped_column(Boolean)
    complaint_filed: Mapped[bool] = mapped_column(Boolean)
    illegal_dumping_flag: Mapped[bool] = mapped_column(Boolean)
    service_completion_time_min: Mapped[float | None] = mapped_column(Float, nullable=True)
