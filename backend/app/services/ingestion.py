import hashlib
import json
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "Station",
    "District",
    "Latitude",
    "Longitude",
    "Data Acquisition Time",
    "Groundwater Level Telemetry 6 Hourly (meter)",
]

DATE_COL = "Data Acquisition Time"
LEVEL_COL = "Groundwater Level Telemetry 6 Hourly (meter)"
STATION_KEY = ["Station", "District", "Latitude", "Longitude"]

NUMERIC_COLUMNS = [
    "Latitude",
    "Longitude",
    "RL_MSL",
    LEVEL_COL,
]


def station_identifier(row):
    """Create a deterministic ID from station name and location."""
    values = [
        str(row[col]).strip()
        for col in STATION_KEY
    ]
    raw_key = "|".join(values).lower()
    return hashlib.sha256(raw_key.encode()).hexdigest()[:16]


def process_csv(input_path, output_path, report_path):
    input_path = Path(input_path)
    output_path = Path(output_path)
    report_path = Path(report_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Dataset not found: {input_path}")

    df = pd.read_csv(input_path)
    original_rows = len(df)

    # Validate required columns
    missing_columns = [
        col for col in REQUIRED_COLUMNS if col not in df.columns
    ]
    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # Convert dash placeholders to missing values in memory only
    df = df.replace(r"^\s*-\s*$", pd.NA, regex=True)

    # Convert numeric fields
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Parse timestamps
    df[DATE_COL] = pd.to_datetime(
        df[DATE_COL],
        format="%d-%m-%Y %H:%M",
        errors="coerce"
    )

    # Validate required station and measurement fields
    invalid_station = df[STATION_KEY].isna().any(axis=1)
    invalid_timestamp = df[DATE_COL].isna()
    invalid_measurement = df[LEVEL_COL].isna()

    # Create station IDs only where station identity is available
    df["station_id"] = pd.NA
    valid_identity = ~invalid_station

    df.loc[valid_identity, "station_id"] = (
        df.loc[valid_identity]
        .apply(station_identifier, axis=1)
    )

    # Duplicate station-time records: report, do not delete
    valid_time = valid_identity & ~invalid_timestamp

    duplicate_mask = pd.Series(False, index=df.index)
    duplicate_mask.loc[valid_time] = df.loc[valid_time].duplicated(
        STATION_KEY + [DATE_COL],
        keep=False
    )

    # Calculate sampling intervals per station
    valid_observations = df.loc[
        valid_time, ["station_id", DATE_COL]
    ].sort_values(["station_id", DATE_COL])

    intervals = (
        valid_observations.groupby("station_id")[DATE_COL]
        .diff()
        .dropna()
        .dt.total_seconds()
        .div(3600)
    )

    interval_counts = {
        str(float(key)): int(value)
        for key, value in intervals.value_counts().items()
    }

    # Save processed copy; preserve all original rows
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False)

    report = {
        "input_file": str(input_path),
        "processed_file": str(output_path),
        "original_rows": int(original_rows),
        "processed_rows": int(len(df)),
        "columns": list(df.columns),
        "unique_station_ids": int(df["station_id"].nunique()),
        "missing_required_columns": missing_columns,
        "invalid_station_identity_rows": int(invalid_station.sum()),
        "invalid_timestamps": int(invalid_timestamp.sum()),
        "missing_or_invalid_measurements": int(
            invalid_measurement.sum()
        ),
        "duplicate_station_time_rows": int(duplicate_mask.sum()),
        "duplicate_station_time_groups": int(
            df.loc[duplicate_mask].groupby(
                STATION_KEY + [DATE_COL]
            ).ngroups
        ),
        "sampling_interval_hours": interval_counts,
        "rows_removed": 0,
        "raw_file_modified": False,
        "notes": [
            "Dash placeholders are converted to missing values "
            "in the processed copy.",
            "Suspicious measurements are retained.",
            "Duplicate records are reported, not deleted.",
            "Six-hour sampling is a provisional expectation.",
            "Station IDs are provisional composite identifiers."
        ]
    }

    with report_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, default=str)

    print("\n========== INGESTION COMPLETE ==========")
    print("Original rows:", original_rows)
    print("Processed rows:", len(df))
    print("Unique station IDs:", report["unique_station_ids"])
    print("Invalid timestamps:", report["invalid_timestamps"])
    print("Invalid measurements:", report[
        "missing_or_invalid_measurements"
    ])
    print("Duplicate station-time rows:", report[
        "duplicate_station_time_rows"
    ])
    print("Processed CSV:", output_path)
    print("Validation report:", report_path)


if __name__ == "__main__":
    process_csv(
        "../datasets/raw/maha.csv",
        "../datasets/processed/maha_validated.csv",
        "../datasets/processed/validation_report.json"
    )
