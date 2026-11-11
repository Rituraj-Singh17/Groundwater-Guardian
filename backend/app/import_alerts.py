import ast
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

from app.database import engine, SessionLocal
from app.models import Alert, Station


SOURCE = Path("../datasets/processed/detection_results.csv")
BATCH_SIZE = 1000


def parse_evidence(value):
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return {}

    try:
        result = ast.literal_eval(value)
        return result if isinstance(result, dict) else {}
    except (ValueError, SyntaxError):
        return {}


def main():
    df = pd.read_csv(SOURCE, low_memory=False)

    required = {
        "station_id", "alert_type", "severity",
        "start_time", "end_time", "message", "evidence"
    }

    if not required.issubset(df.columns):
        raise ValueError(
            f"Missing CSV columns: {sorted(required - set(df.columns))}"
        )

    df["station_id"] = df["station_id"].astype(str)
    df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce")
    df["end_time"] = pd.to_datetime(df["end_time"], errors="coerce")

    if df[["station_id", "alert_type", "severity", "start_time",
           "end_time", "message"]].isna().any().any():
        raise ValueError("CSV contains missing required alert values.")

    duplicates = df.duplicated(
        subset=["station_id", "alert_type", "start_time"]
    ).sum()

    if duplicates:
        raise ValueError(
            f"Found {duplicates} duplicate alert identities. "
            "Import stopped to avoid merging distinct events."
        )

    with engine.begin() as connection:
        connection.execute(text("""
            ALTER TABLE alerts
            ADD COLUMN IF NOT EXISTS start_at TIMESTAMP
        """))
        connection.execute(text("""
            ALTER TABLE alerts
            ADD COLUMN IF NOT EXISTS end_at TIMESTAMP
        """))
        connection.execute(text("""
            ALTER TABLE alerts
            ADD COLUMN IF NOT EXISTS evidence JSON
        """))

        station_ids = set(df["station_id"].unique())
        existing_ids = set(
            connection.execute(
                text("SELECT station_id FROM stations")
            ).scalars().all()
        )

        unknown = station_ids - existing_ids

        if unknown:
            raise ValueError(
                f"{len(unknown)} station IDs are missing from PostgreSQL. "
                f"Examples: {list(unknown)[:5]}"
            )

        connection.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_alert_identity
            ON alerts (station_id, alert_type, detected_at)
        """))

    records = []

    for row in df.itertuples(index=False):
        records.append({
            "station_id": row.station_id,
            "alert_type": row.alert_type,
            "severity": row.severity,
            "explanation": row.message,
            "status": "open",
            "detected_at": row.start_time.to_pydatetime(),
            "start_at": row.start_time.to_pydatetime(),
            "end_at": row.end_time.to_pydatetime(),
            "evidence": parse_evidence(row.evidence)
        })

    inserted = 0

    with engine.begin() as connection:
        for start in range(0, len(records), BATCH_SIZE):
            batch = records[start:start + BATCH_SIZE]

            statement = insert(Alert).values(batch)
            statement = statement.on_conflict_do_nothing(
                index_elements=[
                    Alert.station_id,
                    Alert.alert_type,
                    Alert.detected_at
                ]
            )

            result = connection.execute(statement)
            inserted += result.rowcount

            print(
                f"Processed {min(start + BATCH_SIZE, len(records))}"
                f"/{len(records)} alerts"
            )

    with SessionLocal() as db:
        total = db.query(Alert).count()
        open_count = db.query(Alert).filter(Alert.status == "open").count()

    print("\\n========== ALERT IMPORT COMPLETE ==========")
    print("CSV alerts:", len(records))
    print("Newly inserted:", inserted)
    print("Existing alerts skipped:", len(records) - inserted)
    print("Total alerts in database:", total)
    print("Open alerts:", open_count)


if __name__ == "__main__":
    main()
