from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import Station, StationReliability
from app.schemas import (
    StationListItem,
    StationListResponse,
    StationDetail,
    ReliabilityResponse
)

router = APIRouter(
    prefix="/api/stations",
    tags=["Stations"]
)


@router.get("", response_model=StationListResponse)
def list_stations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    district: str | None = None,
    category: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db)
):
    query = (
        db.query(Station, StationReliability)
        .outerjoin(
            StationReliability,
            Station.station_id == StationReliability.station_id
        )
    )

    if district:
        query = query.filter(Station.district.ilike(f"%{district}%"))

    if category:
        query = query.filter(
            StationReliability.reliability_category.ilike(category)
        )

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Station.station_name.ilike(pattern),
                Station.station_id.ilike(pattern),
                Station.district.ilike(pattern)
            )
        )

    total = query.count()

    rows = (
        query.order_by(Station.station_name)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    stations = []

    for station, reliability in rows:
        stations.append({
            "station_id": station.station_id,
            "station_name": station.station_name,
            "district": station.district,
            "state": station.state,
            "latitude": station.latitude,
            "longitude": station.longitude,
            "reliability_score": (
                reliability.reliability_score if reliability else None
            ),
            "reliability_category": (
                reliability.reliability_category if reliability else None
            ),
            "investigation_priority": (
                reliability.investigation_priority if reliability else None
            )
        })

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "stations": stations
    }


@router.get("/{station_id}", response_model=StationDetail)
def get_station(
    station_id: str,
    db: Session = Depends(get_db)
):
    station = (
        db.query(Station)
        .filter(Station.station_id == station_id)
        .first()
    )

    if station is None:
        raise HTTPException(status_code=404, detail="Station not found")

    return station


@router.get(
    "/{station_id}/reliability",
    response_model=ReliabilityResponse
)
def get_station_reliability(
    station_id: str,
    db: Session = Depends(get_db)
):
    reliability = (
        db.query(StationReliability)
        .filter(StationReliability.station_id == station_id)
        .first()
    )

    if reliability is None:
        exists = (
            db.query(Station.station_id)
            .filter(Station.station_id == station_id)
            .first()
        )

        if exists is None:
            raise HTTPException(status_code=404, detail="Station not found")

        raise HTTPException(
            status_code=404,
            detail="Reliability score not available for this station"
        )

    return reliability
