from pathlib import Path

import pandas as pd
from sqlalchemy import insert
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database import engine
from app.models import Station, Observation


ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "datasets" / "processed" / "maha_validated.csv"
BATCH_SIZE = 10000

def clean(value):
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {CSV_PATH}")

    print("Starting groundwater data import...")
    print("Source:", CSV_PATH)

    total_read = 0
    stations_inserted = 0
    observations_inserted = 0
    invalid_rows = 0

    required = [
        "Station", "station_id", "Agency", "State LGD Code",
        "State", "District LGD Code", "District", "Latitude",
        "Longitude", "RL_MSL", "SlNo", "Data Acquisition Time",
        "Groundwater Level Telemetry 6 Hourly (meter)"
    ]

    for chunk in pd.read_csv(CSV_PATH, chunksize=BATCH_SIZE):
        missing = set(required) - set(chunk.columns)
        if missing:
            raise ValueError(f"Missing columns: {sorted(missing)}")

        total_read += len(chunk)

        chunk["parsed_time"] = pd.to_datetime(
            chunk["Data Acquisition Time"], errors="coerce"
        )
        chunk["parsed_level"] = pd.to_numeric(
            chunk["Groundwater Level Telemetry 6 Hourly (meter)"],
            errors="coerce"
        )

        valid = chunk[
            chunk["station_id"].notna()
            & chunk["parsed_time"].notna()
            & chunk["parsed_level"].notna()
        ].copy()

        invalid_rows += len(chunk) - len(valid)

        if valid.empty:
            continue

        # One station record per station ID in this batch
        station_data = valid.drop_duplicates("station_id")

        station_rows = []
        for row in station_data.to_dict("records"):
            station_rows.append({
                "station_id": str(row["station_id"]),
                "station_name": str(row["Station"]),
                "agency": clean(row["Agency"]),
                "state_lgd_code": clean(row["State LGD Code"]),
                "state": clean(row["State"]),
                "district_lgd_code": clean(row["District LGD Code"]),
                "district": clean(row["District"]),
                "latitude": clean(row["Latitude"]),
                "longitude": clean(row["Longitude"]),
                "rl_msl": clean(row["RL_MSL"])
            })

        observation_rows = []
        for row in valid.to_dict("records"):
            observation_rows.append({
                "station_id": str(row["station_id"]),
                "source_slno": clean(row["SlNo"]),
                "observed_at": row["parsed_time"].to_pydatetime(),
                "groundwater_level_m": float(row["parsed_level"])
            })

        # Insert each batch atomically
        with engine.begin() as connection:
            station_stmt = (
                pg_insert(Station)
                .values(station_rows)
                .on_conflict_do_nothing(
                    index_elements=["station_id"]
                )
                .returning(Station.station_id)
            )

            stations_inserted += len(
                connection.execute(station_stmt).fetchall()
            )

            observation_stmt = (
                pg_insert(Observation)
                .values(observation_rows)
                .on_conflict_do_nothing(
                    index_elements=["station_id", "observed_at"]
                )
                .returning(Observation.id)
            )

            observations_inserted += len(
                connection.execute(observation_stmt).fetchall()
            )

        print(
            f"Processed {total_read:,} rows | "
            f"Observations inserted: {observations_inserted:,}"
        )

    print("\n========== IMPORT COMPLETE ==========")
    print("Rows read:", f"{total_read:,}")
    print("New stations:", f"{stations_inserted:,}")
    print("New observations:", f"{observations_inserted:,}")
    print("Invalid rows skipped:", f"{invalid_rows:,}")
    print("Existing records were preserved.")


if __name__ == "__main__":
    main()
