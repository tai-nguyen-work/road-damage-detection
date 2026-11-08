from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    database: Literal["ok", "error"]
    postgis: Literal["ok", "error"]
    schema_status: Literal["ok", "error"] = Field(alias="schema")
    redis: Literal["ok", "error"]
