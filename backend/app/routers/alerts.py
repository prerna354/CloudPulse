from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Alert, User
from app.schemas import AlertOut, AlertPage

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


def _to_out(alert: Alert) -> AlertOut:
    return AlertOut(
        id=alert.id,
        service_id=alert.service_id,
        service_name=alert.service.name,
        severity=alert.severity,
        message=alert.message,
        created_at=alert.created_at,
        resolved_at=alert.resolved_at,
        acknowledged=alert.acknowledged,
    )


@router.get("", response_model=AlertPage)
def list_alerts(
    active_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    conditions = [Alert.resolved_at.is_(None)] if active_only else []
    total = db.scalar(select(func.count()).select_from(Alert).where(*conditions)) or 0
    alerts = db.scalars(
        select(Alert).where(*conditions).order_by(Alert.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return AlertPage(items=[_to_out(a) for a in alerts], total=total, page=page, page_size=page_size)


@router.post("/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    alert.acknowledged = True
    db.commit()
    return _to_out(alert)
