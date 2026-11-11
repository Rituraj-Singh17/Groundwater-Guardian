import ast
import math
import pandas as pd


DEFAULT_WEIGHTS = {
    "missing": 0.40,
    "flatline": 0.30,
    "sudden": 0.20,
    "completeness": 0.10
}

DEFAULT_PENALTIES = {
    "missing": 0.25,
    "flatline": 2.5,
    "sudden": 5.0
}


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


def score_stations(
    observations,
    alerts,
    weights=None,
    penalties=None,
    expected_interval_hours=6
):
    weights = weights or DEFAULT_WEIGHTS
    penalties = penalties or DEFAULT_PENALTIES

    if set(weights) != set(DEFAULT_WEIGHTS):
        raise ValueError("Invalid scoring weight keys")

    if not math.isclose(sum(weights.values()), 1.0):
        raise ValueError("Scoring weights must sum to 1.0")

    if expected_interval_hours <= 0:
        raise ValueError("Expected interval must be positive")

    data = observations.copy()

    required = {
        "station_id", "observed_at", "groundwater_level_m"
    }

    if not required.issubset(data.columns):
        raise ValueError("Missing required observation columns")

    data["station_id"] = data["station_id"].astype(str)
    data["observed_at"] = pd.to_datetime(
        data["observed_at"], errors="coerce"
    )
    data["groundwater_level_m"] = pd.to_numeric(
        data["groundwater_level_m"], errors="coerce"
    )

    data = data.dropna(subset=["station_id", "observed_at"])

    if alerts is None or alerts.empty:
        alerts = pd.DataFrame(
            columns=["station_id", "alert_type", "evidence"]
        )
    else:
        alerts = alerts.copy()
        alerts["station_id"] = alerts["station_id"].astype(str)

    rows = []

    for station, group in data.groupby("station_id"):
        group = group.sort_values("observed_at")

        first_time = group["observed_at"].min()
        last_time = group["observed_at"].max()

        span_hours = (
            last_time - first_time
        ).total_seconds() / 3600

        expected_count = max(
            1,
            math.floor(span_hours / expected_interval_hours) + 1
        )

        total_rows = len(group)
        valid_rows = int(group["groundwater_level_m"].notna().sum())

        station_alerts = alerts[
            alerts["station_id"] == station
        ]

        missing_alerts = station_alerts[
            station_alerts["alert_type"] == "missing_readings"
        ]

        flatline_alerts = station_alerts[
            station_alerts["alert_type"].isin(
                ["flatline", "repeated_readings"]
            )
        ]

        sudden_alerts = station_alerts[
            station_alerts["alert_type"] == "sudden_change"
        ]

        # Estimate missing observations using detection evidence.
        estimated_missing = sum(
            max(
                0,
                float(
                    parse_evidence(value).get(
                        "estimated_missing_readings", 0
                    )
                )
            )
            for value in missing_alerts.get(
                "evidence", pd.Series(dtype=object)
            )
        )

        missing_rate = estimated_missing / expected_count * 1000
        flatline_rate = len(flatline_alerts) / expected_count * 1000
        sudden_rate = len(sudden_alerts) / expected_count * 1000

        # Gradual, configurable quality penalties.
        missing_quality = max(
            0, 100 - missing_rate * penalties["missing"]
        )

        flatline_quality = max(
            0, 100 - flatline_rate * penalties["flatline"]
        )

        sudden_quality = max(
            0, 100 - sudden_rate * penalties["sudden"]
        )

        completeness = min(
            100, valid_rows / expected_count * 100
        )

        final_score = (
            missing_quality * weights["missing"]
            + flatline_quality * weights["flatline"]
            + sudden_quality * weights["sudden"]
            + completeness * weights["completeness"]
        )

        if final_score >= 80:
            category = "High"
        elif final_score >= 60:
            category = "Moderate"
        elif final_score >= 40:
            category = "Low"
        else:
            category = "Very Low"

        rows.append({
            "station_id": station,
            "total_observations": total_rows,
            "expected_observations": expected_count,
            "valid_observations": valid_rows,
            "estimated_missing_observations": round(
                estimated_missing, 2
            ),
            "missing_alerts": len(missing_alerts),
            "flatline_repeated_alerts": len(flatline_alerts),
            "sudden_change_alerts": len(sudden_alerts),
            "missing_rate_per_1000": round(missing_rate, 2),
            "flatline_rate_per_1000": round(flatline_rate, 2),
            "sudden_rate_per_1000": round(sudden_rate, 2),
            "missing_quality": round(missing_quality, 2),
            "flatline_quality": round(flatline_quality, 2),
            "sudden_quality": round(sudden_quality, 2),
            "completeness": round(completeness, 2),
            "reliability_score": round(final_score, 2),
            "reliability_category": category
        })

    return pd.DataFrame(rows).sort_values(
        "reliability_score", ascending=True
    ).reset_index(drop=True)
