from sqlalchemy import func

from app.database import SessionLocal
from app.models import StationReliability


db = SessionLocal()

try:
    total = db.query(StationReliability).count()

    print("\n========== RELIABILITY DATABASE VERIFICATION ==========")
    print("Stored station records:", total)

    print("\nCategories:")
    categories = (
        db.query(
            StationReliability.reliability_category,
            func.count(StationReliability.station_id)
        )
        .group_by(StationReliability.reliability_category)
        .all()
    )

    for category, count in categories:
        print(f"{category}: {count}")

    print("\nInvestigation priorities:")
    priorities = (
        db.query(
            StationReliability.investigation_priority,
            func.count(StationReliability.station_id)
        )
        .group_by(StationReliability.investigation_priority)
        .all()
    )

    for priority, count in priorities:
        print(f"{priority}: {count}")

    print("\nLowest five reliability scores:")
    lowest = (
        db.query(StationReliability)
        .order_by(StationReliability.reliability_score.asc())
        .limit(5)
        .all()
    )

    for row in lowest:
        print(
            row.station_id,
            row.reliability_score,
            row.reliability_category,
            row.primary_concern,
            row.investigation_priority
        )

finally:
    db.close()
