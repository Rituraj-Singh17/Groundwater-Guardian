import pandas as pd
import pytest
from app.services.detection import detect_anomalies


def make_data(values, hours=None):
    if hours is None:
        hours = [i * 6 for i in range(len(values))]

    return pd.DataFrame({
        "station_id": ["TEST-1"] * len(values),
        "observed_at": [
            pd.Timestamp("2025-01-01") + pd.Timedelta(hours=h)
            for h in hours
        ],
        "groundwater_level_m": values
    })


def test_missing_readings():
    alerts = detect_anomalies(make_data([-10, -11, -12], [0, 6, 24]))
    assert any(a["alert_type"] == "missing_readings" for a in alerts)


def test_repeated_readings():
    alerts = detect_anomalies(make_data([-10, -10, -10]))
    assert any(a["alert_type"] == "repeated_readings" for a in alerts)


def test_flatline():
    alerts = detect_anomalies(make_data([-10] * 6))
    assert any(a["alert_type"] == "flatline" for a in alerts)


def test_sudden_change():
    alerts = detect_anomalies(make_data([-10, -25]))
    assert any(a["alert_type"] == "sudden_change" for a in alerts)


def test_normal_data():
    alerts = detect_anomalies(make_data([-10, -10.5, -11]))
    assert len(alerts) == 0


def test_invalid_columns():
    with pytest.raises(ValueError):
        detect_anomalies(pd.DataFrame({"wrong_column": [1, 2]}))


def test_rapid_readings_not_flatline():
    alerts = detect_anomalies(
        make_data([-10] * 20, [i / 60 for i in range(20)])
    )
    assert not any(
        a["alert_type"] in ["flatline", "repeated_readings"]
        for a in alerts
    )


def test_flatline_requires_continuous_intervals():
    alerts = detect_anomalies(
        make_data([-10] * 6, [0, 6, 12, 48, 54, 60])
    )
    assert not any(a["alert_type"] == "flatline" for a in alerts)
