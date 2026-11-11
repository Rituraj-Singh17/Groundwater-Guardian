import pandas as pd

REQUIRED_COLUMNS = {
    "station_id",
    "observed_at",
    "groundwater_level_m"
}


def detect_anomalies(
    df,
    expected_interval_hours=6,
    jump_threshold_m=10.0,
    flatline_tolerance_m=0.001,
    interval_tolerance_hours=3.0
):
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    data = df.copy()
    data["observed_at"] = pd.to_datetime(
        data["observed_at"], errors="coerce"
    )
    data["groundwater_level_m"] = pd.to_numeric(
        data["groundwater_level_m"], errors="coerce"
    )

    data = data.dropna(
        subset=["station_id", "observed_at", "groundwater_level_m"]
    )
    data = data.sort_values(["station_id", "observed_at"])

    expected = pd.Timedelta(hours=expected_interval_hours)
    min_interval = expected - pd.Timedelta(hours=interval_tolerance_hours)
    max_interval = expected + pd.Timedelta(hours=interval_tolerance_hours)

    alerts = []

    def add_alert(station, kind, severity, start, end, message, evidence):
        alerts.append({
            "station_id": str(station),
            "alert_type": kind,
            "severity": severity,
            "start_time": start,
            "end_time": end,
            "message": message,
            "evidence": evidence
        })

    for station, group in data.groupby("station_id"):
        group = group.reset_index(drop=True)
        times = group["observed_at"]
        levels = group["groundwater_level_m"]

        # 1. Missing expected observations
        for i in range(1, len(group)):
            gap = times.iloc[i] - times.iloc[i - 1]

            if gap > max_interval:
                estimated = max(
                    round(gap / expected) - 1, 1
                )

                hours = gap.total_seconds() / 3600

                add_alert(
                    station,
                    "missing_readings",
                    "high" if estimated >= 3 else "medium",
                    times.iloc[i - 1],
                    times.iloc[i],
                    f"Observation gap of {hours:.1f} hours. "
                    f"Approximately {estimated} readings may be missing.",
                    {
                        "gap_hours": hours,
                        "estimated_missing_readings": estimated,
                        "extended_gap": hours >= 24 * 30
                    }
                )

        # 2. Repeated readings and flatlines
        run_start = 0

        for i in range(1, len(group) + 1):
            if i < len(group):
                gap = times.iloc[i] - times.iloc[i - 1]

                continuous = min_interval <= gap <= max_interval
                same_value = (
                    abs(levels.iloc[i] - levels.iloc[i - 1])
                    <= flatline_tolerance_m
                )
            else:
                continuous = False
                same_value = False

            if not (continuous and same_value):
                count = i - run_start
                start = times.iloc[run_start]
                end = times.iloc[i - 1]
                duration = (end - start).total_seconds() / 3600
                value = float(levels.iloc[run_start])

                if count >= 6 and duration >= 30:
                    add_alert(
                        station,
                        "flatline",
                        "high",
                        start,
                        end,
                        f"Reading remained nearly constant at {value} m "
                        f"for {count} observations across {duration:.1f} hours.",
                        {
                            "reading_m": value,
                            "consecutive_observations": count,
                            "duration_hours": duration
                        }
                    )

                elif count >= 3 and duration >= 12:
                    add_alert(
                        station,
                        "repeated_readings",
                        "low",
                        start,
                        end,
                        f"Reading {value} m repeated across "
                        f"{count} observations over {duration:.1f} hours.",
                        {
                            "reading_m": value,
                            "consecutive_observations": count,
                            "duration_hours": duration
                        }
                    )

                run_start = i

        # 3. Sudden changes across near-scheduled observations
        for i in range(1, len(group)):
            gap = times.iloc[i] - times.iloc[i - 1]

            if min_interval <= gap <= max_interval:
                change = float(levels.iloc[i] - levels.iloc[i - 1])

                if abs(change) > jump_threshold_m:
                    add_alert(
                        station,
                        "sudden_change",
                        "medium",
                        times.iloc[i - 1],
                        times.iloc[i],
                        f"Groundwater level changed by {change:.3f} m. "
                        "This may be genuine or a data-quality issue.",
                        {
                            "previous_reading_m": float(levels.iloc[i - 1]),
                            "current_reading_m": float(levels.iloc[i]),
                            "change_m": change
                        }
                    )

    return alerts
