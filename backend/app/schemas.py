from typing import Optional, List
from pydantic import BaseModel, ConfigDict
import datetime


class ScanCreate(BaseModel):
    target_type: str  # repo | zip | image | binary | local
    target_ref: str


class ScanStatus(BaseModel):
    id: int
    status: str
    progress_message: str
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class FindingOut(BaseModel):
    id: int
    quantum_vulnerable: bool
    broken_by: Optional[str] = None
    risk_level: str
    mosca_x: float
    mosca_y: float
    mosca_z: float
    at_risk: bool
    explanation: Optional[str] = None
    recommendation_summary: Optional[str] = None
    recommendation_detail: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AssetOut(BaseModel):
    id: int
    asset_type: str
    name: Optional[str] = None
    algorithm: Optional[str] = None
    category: Optional[str] = None
    key_size: Optional[int] = None
    mode: Optional[str] = None
    language: Optional[str] = None
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    raw_snippet: Optional[str] = None
    criticality_tag: str
    finding: Optional[FindingOut] = None

    model_config = ConfigDict(from_attributes=True)


class ScanSummary(BaseModel):
    id: int
    target_type: str
    target_ref: str
    status: str
    created_at: datetime.datetime
    counts: dict

    model_config = ConfigDict(from_attributes=True)


class CriticalityUpdate(BaseModel):
    criticality_tag: str


class MoscaZUpdate(BaseModel):
    z_years: float
