"""Daily operational outcome model."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.smart_bin import SmartBin


class OperationalDaily(Base):
    """Bin-level daily service outcome from ``operational_daily.csv``."""

    __tablename__ = "operational_daily"
    __table_args__ = (
        UniqueConstraint("bin_id", "date", name="uq_operational_daily_bin_date"),
        CheckConstraint(
            "service_completion_time_min IS NULL OR service_completion_time_min >= 0",
            name="ck_operational_daily_completion_nonnegative",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bin_id: Mapped[str] = mapped_column(ForeignKey("smart_bins.bin_id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    governorate: Mapped[str] = mapped_column(String(120), nullable=False)
    region: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    missed_collection: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    emergency_request: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    complaint_filed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    illegal_dumping_flag: Mapped[bool] = mapped_column(Boolean, nullable=False)
    service_completion_time_min: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    smart_bin: Mapped["SmartBin"] = relationship(back_populates="operational_records", lazy="raise")
