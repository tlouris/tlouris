from datetime import datetime
from pydantic import BaseModel, Field


class MeterBase(BaseModel):
    meter_id: str
    name: str
    basin: str
    gis_link: str | None = None
    pipe_diameter_in: float | None = None
    slope: float | None = None
    mannings_n: float | None = None
    capacity_mgd: float | None = None
    status: str = "active"


class MeterCreate(MeterBase):
    pass


class MeterRead(MeterBase):
    id: int

    class Config:
        from_attributes = True


class SeriesPoint(BaseModel):
    timestamp_utc: datetime
    flow_mgd: float
    utilization_pct: float = Field(..., description="Flow utilization relative to capacity")
    exceedance: bool


class MeterSummary(BaseModel):
    meter_id: str
    avg_flow_mgd: float
    min_flow_mgd: float
    max_flow_mgd: float
    p95_flow_mgd: float
    p99_flow_mgd: float
    avg_utilization_pct: float
    peak_utilization_pct: float
    total_volume_mg: float
    count_exceedances: int


class AnomalyRead(BaseModel):
    anomaly_type: str
    severity: int
    start_time: datetime
    end_time: datetime
    peak_value: float | None = None
    explanation: str

    class Config:
        from_attributes = True
