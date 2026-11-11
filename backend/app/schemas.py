from pydantic import BaseModel, ConfigDict
from typing import Optional


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class DashboardSummary(BaseModel):
    total_stations: int
    total_observations: int
    total_alerts: int
    open_alerts: int
    maintenance_records: int
    reliability_categories: dict[str, int]


class StationListItem(ORMModel):
    station_id: str
    station_name: str
    district: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    reliability_score: Optional[float] = None
    reliability_category: Optional[str] = None
    investigation_priority: Optional[str] = None


class StationDetail(ORMModel):
    station_id: str
    station_name: str
    agency: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    rl_msl: Optional[float] = None


class StationListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    stations: list[StationListItem]


class ReliabilityResponse(ORMModel):
    station_id: str
    total_observations: int
    expected_observations: int
    valid_observations: int
    estimated_missing_observations: Optional[float] = None
    missing_alerts: int
    flatline_repeated_alerts: int
    sudden_change_alerts: int
    missing_quality: Optional[float] = None
    flatline_quality: Optional[float] = None
    sudden_quality: Optional[float] = None
    completeness: Optional[float] = None
    missing_quality_contribution: Optional[float] = None
    flatline_quality_contribution: Optional[float] = None
    sudden_quality_contribution: Optional[float] = None
    completeness_contribution: Optional[float] = None
    reliability_score: float
    reliability_category: str
    primary_concern: Optional[str] = None
    explanation: Optional[str] = None
    recommended_action: Optional[str] = None
    investigation_priority: Optional[str] = None

from datetime import datetime
from typing import Optional, Literal
from pydantic import Field


class AlertResponse(BaseModel):
    id: int
    station_id: str
    observation_id: Optional[int] = None
    alert_type: str
    severity: str
    explanation: str
    status: str
    detected_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class AlertListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    alerts: list[AlertResponse]


class MaintenanceCreate(BaseModel):
    alert_id: int
    assigned_to: Optional[str] = Field(default=None, max_length=150)
    notes: Optional[str] = None


class MaintenanceUpdate(BaseModel):
    status: Optional[Literal["open", "investigating", "resolved"]] = None
    assigned_to: Optional[str] = Field(default=None, max_length=150)
    notes: Optional[str] = None


class MaintenanceResponse(BaseModel):
    id: int
    alert_id: int
    assigned_to: Optional[str] = None
    status: str
    notes: Optional[str] = None
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None


class MaintenanceListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    maintenance_records: list[MaintenanceResponse]
