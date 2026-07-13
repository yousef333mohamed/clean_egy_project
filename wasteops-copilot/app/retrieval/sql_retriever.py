"""Safe structured-data retrieval."""

import json
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import Settings
from app.core.security import validate_read_only_sql
from app.schemas.retrieval import Evidence
from app.services.llm_service import LLMService

SCHEMA = """smart_bins(bin_id,governorate,region,latitude,longitude,capacity_liters,primary_waste_type,install_date)
smart_bin_readings(bin_id,timestamp,fill_level_pct,waste_weight_kg,waste_type,temperature_c,humidity_pct,battery_level_pct,sensor_status,was_collected)
trucks(truck_id,region,capacity_kg,model_year,fuel_type)
truck_trip_logs(truck_id,date,region,status,distance_km,fuel_consumed_l,load_kg,avg_speed_kmh,stops_completed,trip_duration_min)
workforce(worker_id,governorate,region,shift,experience_years)
workforce_attendance(worker_id,date,present,completed_tasks,overtime_hours,performance_score)
operational_daily(bin_id,date,governorate,region,missed_collection,emergency_request,complaint_filed,illegal_dumping_flag,service_completion_time_min)
environmental_daily(date,region,temperature_c,rainfall_mm,is_holiday,is_festival,is_weekend,traffic_level)"""


class SQLRetriever:
    """Generate, validate, and execute read-only analytical SQL."""

    def __init__(self, session: AsyncSession, llm: LLMService, settings: Settings) -> None:
        self.session = session
        self.llm = llm
        self.settings = settings

    async def retrieve(self, question: str) -> list[Evidence]:
        """Return database rows as normalized evidence."""
        if not self.settings.llm_api_key:
            return []
        sql = await self.llm.complete(self.llm.prompt("sql_generation_prompt.txt"), f"Schema:\n{SCHEMA}\nQuestion:\n{question}")
        sql = sql.removeprefix("```sql").removesuffix("```").strip()
        safe = validate_read_only_sql(sql, self.settings.sql_row_limit)
        await self.session.execute(text("SET TRANSACTION READ ONLY"))
        await self.session.execute(
            text("SELECT set_config('statement_timeout', :timeout, true)"),
            {"timeout": f"{self.settings.sql_query_timeout_ms}ms"},
        )
        result = await self.session.execute(text(safe))
        rows = [dict(row._mapping) for row in result]
        return [
            Evidence(
                content=json.dumps(row, default=str, ensure_ascii=False),
                source_type="database",
                source_name="PostgreSQL operational data",
                record_reference=f"query-row:{i + 1}",
                relevance_score=1.0,
            )
            for i, row in enumerate(rows)
        ]
