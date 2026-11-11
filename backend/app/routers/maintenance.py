from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert, MaintenanceRecord
from app.schemas import (
    MaintenanceCreate,
    MaintenanceUpdate,
    MaintenanceResponse,
    MaintenanceListResponse
)

router = APIRouter(
    prefix="/api/maintenance",
    tags=["Maintenance"]
)


@router.get("", response_model=MaintenanceListResponse)
def list_maintenance(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    assigned_to: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(MaintenanceRecord)

    if status:
        query = query.filter(MaintenanceRecord.status.ilike(status))

    if assigned_to:
        query = query.filter(
            MaintenanceRecord.assigned_to.ilike(f"%{assigned_to}%")
        )

    total = query.count()

    records = (
        query.order_by(MaintenanceRecord.opened_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "maintenance_records": records
    }


@router.post("", response_model=MaintenanceResponse, status_code=201)
def create_maintenance(
    payload: MaintenanceCreate,
    db: Session = Depends(get_db)
):
    alert = (
        db.query(Alert)
        .filter(Alert.id == payload.alert_id)
        .first()
    )

    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    record = MaintenanceRecord(
        alert_id=payload.alert_id,
        assigned_to=payload.assigned_to,
        notes=payload.notes,
        status="open"
    )

    try:
        db.add(record)
        alert.status = "investigating"
        alert.resolved_at = None
        db.commit()
        db.refresh(record)
    except Exception:
        db.rollback()
        raise

    return record


@router.patch("/{maintenance_id}", response_model=MaintenanceResponse)
def update_maintenance(
    maintenance_id: int,
    payload: MaintenanceUpdate,
    db: Session = Depends(get_db)
):
    record = (
        db.query(MaintenanceRecord)
        .filter(MaintenanceRecord.id == maintenance_id)
        .first()
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Maintenance record not found"
        )

    updates = payload.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(
            status_code=400,
            detail="No update fields provided"
        )

    alert = (
        db.query(Alert)
        .filter(Alert.id == record.alert_id)
        .first()
    )

    for field, value in updates.items():
        setattr(record, field, value)

    if "status" in updates:
        if record.status == "resolved":
            record.closed_at = datetime.now()
            if alert:
                alert.status = "resolved"
                alert.resolved_at = record.closed_at
        else:
            record.closed_at = None
            if alert:
                alert.status = "investigating"
                alert.resolved_at = None

    try:
        db.commit()
        db.refresh(record)
    except Exception:
        db.rollback()
        raise

    return record
