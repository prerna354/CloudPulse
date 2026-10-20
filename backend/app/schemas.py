from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=64)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=64)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    full_name: str
    role: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ServiceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    url: HttpUrl
    check_interval_seconds: int = Field(default=30, ge=10, le=3600)
    timeout_ms: int = Field(default=5000, ge=500, le=30000)


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    url: HttpUrl | None = None
    check_interval_seconds: int | None = Field(default=None, ge=10, le=3600)
    timeout_ms: int | None = Field(default=None, ge=500, le=30000)
    is_active: bool | None = None


class ServiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    url: str
    check_interval_seconds: int
    timeout_ms: int
    is_active: bool
    status: str
    consecutive_failures: int
    last_checked_at: datetime | None
    last_response_ms: int | None
    uptime_24h: float | None = None


class ServicePage(BaseModel):
    items: list[ServiceOut]
    total: int
    page: int
    page_size: int


class CheckResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    checked_at: datetime
    is_up: bool
    status_code: int | None
    response_ms: int
    error: str | None


class AlertOut(BaseModel):
    id: int
    service_id: int
    service_name: str
    severity: str
    message: str
    created_at: datetime
    resolved_at: datetime | None
    acknowledged: bool


class AlertPage(BaseModel):
    items: list[AlertOut]
    total: int
    page: int
    page_size: int


class DashboardSummary(BaseModel):
    total_services: int
    up: int
    degraded: int
    down: int
    unknown: int
    active_alerts: int
    avg_response_ms_1h: float | None
    uptime_24h: float | None
