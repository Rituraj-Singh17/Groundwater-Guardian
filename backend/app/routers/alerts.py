from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert
from app.schemas import AlertResponse, AlertListResponse

router = APIRouter(
    prefix="/api/alerts",
    tags=["Alerts"]
)


@router.get("", response_model=AlertListResponse)
def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    station_id: str | None = None,
    alert_type: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(Alert)

    if station_id:
        query = query.filter(Alert.station_id == station_id)

    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)

    if severity:
        query = query.filter(Alert.severity.ilike(severity))

    if status:
        query = query.filter(Alert.status.ilike(status))

    total = query.count()

    alerts = (
        query.order_by(Alert.detected_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "alerts": alerts
    }


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    return alert
