from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_admin
from app.models import CheckResult, MonitoredService, User, utcnow
from app.schemas import CheckResultOut, ServiceCreate, ServiceOut, ServicePage, ServiceUpdate

router = APIRouter(prefix="/api/services", tags=["Services"])


def _get_or_404(db: Session, service_id: int) -> MonitoredService:
    service = db.get(MonitoredService, service_id)
    if service is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Service not found")
    return service


def _uptime_by_service(db: Session, service_ids: list[int]) -> dict[int, float]:
    if not service_ids:
        return {}
    since = utcnow() - timedelta(hours=24)
    rows = db.execute(
        select(CheckResult.service_id, func.avg(case((CheckResult.is_up.is_(True), 1.0), else_=0.0)))
        .where(CheckResult.service_id.in_(service_ids), CheckResult.checked_at >= since)
        .group_by(CheckResult.service_id)
    ).all()
    return {service_id: round(float(avg) * 100, 2) for service_id, avg in rows}


def _to_out(service: MonitoredService, uptime: dict[int, float]) -> ServiceOut:
    out = ServiceOut.model_validate(service)
    out.uptime_24h = uptime.get(service.id)
    return out


@router.get("", response_model=ServicePage)
def list_services(
    q: str | None = Query(None, max_length=100),
    status_filter: str | None = Query(None, alias="status", pattern="^(up|degraded|down|unknown)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    conditions = []
    if q:
        conditions.append(MonitoredService.name.ilike(f"%{q}%"))
    if status_filter:
        conditions.append(MonitoredService.status == status_filter)

    total = db.scalar(select(func.count()).select_from(MonitoredService).where(*conditions)) or 0
    services = db.scalars(
        select(MonitoredService)
        .where(*conditions)
        .order_by(MonitoredService.name)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    uptime = _uptime_by_service(db, [s.id for s in services])
    return ServicePage(items=[_to_out(s, uptime) for s in services], total=total, page=page, page_size=page_size)


@router.post("", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
def create_service(payload: ServiceCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    if db.scalar(select(MonitoredService).where(func.lower(MonitoredService.name) == payload.name.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, "A service with this name already exists")
    service = MonitoredService(
        name=payload.name,
        url=str(payload.url),
        check_interval_seconds=payload.check_interval_seconds,
        timeout_ms=payload.timeout_ms,
    )
    db.add(service)
    db.commit()
    return _to_out(service, {})


@router.get("/{service_id}", response_model=ServiceOut)
def get_service(service_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    service = _get_or_404(db, service_id)
    return _to_out(service, _uptime_by_service(db, [service.id]))


@router.patch("/{service_id}", response_model=ServiceOut)
def update_service(
    service_id: int, payload: ServiceUpdate, db: Session = Depends(get_db), _: User = Depends(require_admin)
):
    service = _get_or_404(db, service_id)
    changes = payload.model_dump(exclude_unset=True)
    if "name" in changes and changes["name"].lower() != service.name.lower():
        if db.scalar(select(MonitoredService).where(func.lower(MonitoredService.name) == changes["name"].lower())):
            raise HTTPException(status.HTTP_409_CONFLICT, "A service with this name already exists")
    if "url" in changes:
        changes["url"] = str(changes["url"])
    for field, value in changes.items():
        setattr(service, field, value)
    db.commit()
    return _to_out(service, _uptime_by_service(db, [service.id]))


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(service_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    service = _get_or_404(db, service_id)
    db.delete(service)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{service_id}/results", response_model=list[CheckResultOut])
def get_results(
    service_id: int,
    limit: int = Query(60, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    _get_or_404(db, service_id)
    rows = db.scalars(
        select(CheckResult).where(CheckResult.service_id == service_id).order_by(CheckResult.checked_at.desc()).limit(limit)
    ).all()
    return list(reversed(rows))
