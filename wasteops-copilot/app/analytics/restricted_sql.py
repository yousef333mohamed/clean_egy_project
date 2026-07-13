"""Disabled preparation contract for a future AST-validated SQL planner."""

from typing import Protocol
from pydantic import BaseModel


class SQLPlan(BaseModel):
    statement: str
    referenced_tables: list[str]
    referenced_columns: list[str]


class RestrictedSQLPlanner(Protocol):
    async def plan(self, question: str, schema_context: str) -> SQLPlan: ...
