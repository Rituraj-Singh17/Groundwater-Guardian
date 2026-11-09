from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import (
    Station,
    Observation,
    Alert,
    MaintenanceRecord,
    StationReliability
)
from app.schemas import DashboardSummary

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"]
)


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)):
    total_stations = db.query(func.count(Station.station_id)).scalar() or 0
    total_observations = db.query(func.count(Observation.id)).scalar() or 0
    total_alerts = db.query(func.count(Alert.id)).scalar() or 0

    open_alerts = (
        db.query(func.count(Alert.id))
        .filter(Alert.status == "open")
        .scalar() or 0
    )

    maintenance_records = (
        db.query(func.count(MaintenanceRecord.id)).scalar() or 0
    )

    category_rows = (
        db.query(
            StationReliability.reliability_category,
            func.count(StationReliability.station_id)
        )
        .group_by(StationReliability.reliability_category)
        .all()
    )

    categories = {
        category: count
        for category, count in category_rows
    }

    return {
        "total_stations": total_stations,
        "total_observations": total_observations,
        "total_alerts": total_alerts,
        "open_alerts": open_alerts,
        "maintenance_records": maintenance_records,
        "reliability_categories": categories
    }
