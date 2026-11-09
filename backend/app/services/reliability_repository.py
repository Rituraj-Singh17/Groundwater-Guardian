import pandas as pd

from app.models import Station, StationReliability


NUMERIC_FIELDS = [
    "estimated_missing_observations",
    "missing_rate_per_1000",
    "flatline_rate_per_1000",
    "sudden_rate_per_1000",
    "missing_quality",
    "flatline_quality",
    "sudden_quality",
    "completeness",
    "missing_quality_contribution",
    "flatline_quality_contribution",
    "sudden_quality_contribution",
    "completeness_contribution",
    "reliability_score"
]

INTEGER_FIELDS = [
    "total_observations",
    "expected_observations",
    "valid_observations",
    "missing_alerts",
    "flatline_repeated_alerts",
    "sudden_change_alerts"
]

TEXT_FIELDS = [
    "reliability_category",
    "primary_concern",
    "explanation",
    "recommended_action",
    "investigation_priority"
]


def save_reliability_scores(db, scores):
    if scores.empty:
        raise ValueError("Cannot save an empty reliability result")

    required = {
        "station_id",
        *NUMERIC_FIELDS,
        *INTEGER_FIELDS,
        *TEXT_FIELDS
    }

    missing = required - set(scores.columns)

    if missing:
        raise ValueError(
            f"Reliability results missing columns: {sorted(missing)}"
        )

    station_ids = scores["station_id"].astype(str).tolist()

    if len(station_ids) != len(set(station_ids)):
        raise ValueError("Duplicate station IDs in reliability results")

    existing_stations = {
        station.station_id
        for station in db.query(Station.station_id)
        .filter(Station.station_id.in_(station_ids))
        .all()
    }

    unknown = set(station_ids) - existing_stations

    if unknown:
        raise ValueError(
            f"Stations not found in database: {sorted(unknown)[:10]}"
        )

    saved = 0
    updated = 0

    try:
        for _, row in scores.iterrows():
            station_id = str(row["station_id"])

            record = db.get(StationReliability, station_id)

            if record is None:
                record = StationReliability(station_id=station_id)
                db.add(record)
                saved += 1
            else:
                updated += 1

            for field in NUMERIC_FIELDS:
                value = row[field]
                setattr(
                    record,
                    field,
                    None if pd.isna(value) else float(value)
                )

            for field in INTEGER_FIELDS:
                value = row[field]
                setattr(
                    record,
                    field,
                    0 if pd.isna(value) else int(value)
                )

            for field in TEXT_FIELDS:
                value = row[field]
                setattr(
                    record,
                    field,
                    None if pd.isna(value) else str(value)
                )

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {"inserted": saved, "updated": updated}
