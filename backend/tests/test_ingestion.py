import json

import pandas as pd
import pytest

from app.services.ingestion import process_csv


def sample_data():
    return pd.DataFrame({
        "Station": ["Station_A", "Station_A"],
        "District": ["Pune", "Pune"],
        "Latitude": [18.52, 18.52],
        "Longitude": [73.85, 73.85],
        "RL_MSL": [500.0, 500.0],
        "Data Acquisition Time": [
            "01-01-2025 00:00",
            "01-01-2025 06:00"
        ],
        "Groundwater Level Telemetry 6 Hourly (meter)": [
            -10.5, -10.6
        ]
    })


def run_pipeline(tmp_path, df):
    source = tmp_path / "input.csv"
    output = tmp_path / "output.csv"
    report = tmp_path / "report.json"

    df.to_csv(source, index=False)
    process_csv(source, output, report)

    return (
        pd.read_csv(output),
        json.loads(report.read_text(encoding="utf-8"))
    )


def test_valid_csv(tmp_path):
    result, report = run_pipeline(tmp_path, sample_data())

    assert len(result) == 2
    assert result["station_id"].nunique() == 1
    assert report["rows_removed"] == 0
    assert report["invalid_timestamps"] == 0


def test_missing_required_column(tmp_path):
    df = sample_data().drop(columns=["Station"])

    with pytest.raises(ValueError, match="Missing required columns"):
        run_pipeline(tmp_path, df)


def test_invalid_timestamp(tmp_path):
    df = sample_data()
    df.loc[0, "Data Acquisition Time"] = "invalid-date"

    result, report = run_pipeline(tmp_path, df)

    assert len(result) == 2
    assert report["invalid_timestamps"] == 1


def test_duplicate_station_time(tmp_path):
    df = sample_data()
    df.loc[1, "Data Acquisition Time"] = "01-01-2025 00:00"

    result, report = run_pipeline(tmp_path, df)

    assert len(result) == 2
    assert report["duplicate_station_time_rows"] == 2
    assert report["duplicate_station_time_groups"] == 1


def test_extreme_measurement_preserved(tmp_path):
    df = sample_data()
    df.loc[0, "Groundwater Level Telemetry 6 Hourly (meter)"] = 7184.31

    result, report = run_pipeline(tmp_path, df)

    assert len(result) == 2
    assert result.loc[0, "Groundwater Level Telemetry 6 Hourly (meter)"] == 7184.31
    assert report["rows_removed"] == 0
