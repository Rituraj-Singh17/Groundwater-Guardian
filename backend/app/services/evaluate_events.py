from pathlib import Path
import pandas as pd

from app.services.detection import detect_anomalies

ROOT = Path("../datasets/processed")
SOURCE = ROOT / "simulated_fault_data.csv"
LABELS = ROOT / "simulation_ground_truth.csv"
BASELINE = ROOT / "detection_results.csv"

FAULT_REPORT = ROOT / "event_level_fault_evaluation.csv"
ALERT_REPORT = ROOT / "event_level_alert_attribution.csv"

TIME = "Data Acquisition Time"
LEVEL = "Groundwater Level Telemetry 6 Hourly (meter)"


def overlaps(a_start, a_end, b_start, b_end):
    return a_start <= b_end and a_end >= b_start


def main():
    df = pd.read_csv(SOURCE, low_memory=False)
    faults = pd.read_csv(LABELS)
    baseline = pd.read_csv(BASELINE)

    df[TIME] = pd.to_datetime(df[TIME], errors="coerce")
    df[LEVEL] = pd.to_numeric(df[LEVEL], errors="coerce")

    data = pd.DataFrame({
        "station_id": df["station_id"],
        "observed_at": df[TIME],
        "groundwater_level_m": df[LEVEL]
    })

    alerts = pd.DataFrame(detect_anomalies(data))

    if alerts.empty:
        raise RuntimeError("No alerts generated.")

    for frame in (alerts, baseline, faults):
        frame["start_time"] = pd.to_datetime(frame["start_time"])
        frame["end_time"] = pd.to_datetime(frame["end_time"])
        frame["station_id"] = frame["station_id"].astype(str)

    alerts["alert_id"] = [
        f"ALERT-{i+1}" for i in range(len(alerts))
    ]

    baseline_groups = {
        (station, kind): group
        for (station, kind), group in baseline.groupby(
            ["station_id", "alert_type"]
        )
    }

    # Identify alerts that overlap same-type baseline alerts.
    alerts["baseline_overlap"] = False

    for i, alert in alerts.iterrows():
        group = baseline_groups.get(
            (alert["station_id"], alert["alert_type"])
        )

        if group is not None:
            alerts.loc[i, "baseline_overlap"] = any(
                overlaps(
                    alert["start_time"], alert["end_time"],
                    row["start_time"], row["end_time"]
                )
                for _, row in group.iterrows()
            )

    # Build fault-level matches.
    used_alerts = set()
    fault_results = []
    alert_links = []

    for _, fault in faults.iterrows():
        station = str(fault["station_id"])
        kind = fault["fault_type"]
        start = fault["start_time"]
        end = fault["end_time"]

        # Sudden spikes may create an entry alert and a recovery alert.
        match_end = end + pd.Timedelta(hours=6) if kind == "sudden_change" else end

        candidates = alerts[
            (alerts["station_id"] == station) &
            (alerts["alert_type"] == kind) &
            (alerts["start_time"] <= match_end) &
            (alerts["end_time"] >= start)
        ]

        candidate_ids = candidates.index.tolist()
        available = [
            i for i in candidate_ids if i not in used_alerts
        ]

        detected = len(available) > 0

        for alert_index in available:
            used_alerts.add(alert_index)
            alert = alerts.loc[alert_index]

            alert_links.append({
                "fault_id": fault["fault_id"],
                "alert_id": alert["alert_id"],
                "fault_type": kind,
                "alert_type": alert["alert_type"],
                "baseline_overlap": alert["baseline_overlap"],
                "attribution": (
                    "baseline_overlapping"
                    if alert["baseline_overlap"]
                    else "new_primary_detection"
                )
            })

        fault_results.append({
            "fault_id": fault["fault_id"],
            "fault_type": kind,
            "station_id": station,
            "detected": detected,
            "matched_alert_count": len(available),
            "matching_alerts": ", ".join(
                alerts.loc[i, "alert_id"] for i in available
            )
        })

    fault_report = pd.DataFrame(fault_results)
    link_report = pd.DataFrame(alert_links)

    # Classify alerts not assigned to an injected fault.
    assigned_ids = set(used_alerts)

    remaining = alerts[~alerts.index.isin(assigned_ids)].copy()

    remaining["attribution"] = "unmatched"
    remaining.loc[
        remaining["baseline_overlap"], "attribution"
    ] = "baseline_overlapping_unmatched"

    # Repeated readings near a missing-data injection are only
    # flagged as possible secondary effects, not confirmed matches.
    for i, alert in remaining.iterrows():
        if alert["alert_type"] != "repeated_readings":
            continue

        nearby = faults[
            (faults["station_id"] == alert["station_id"]) &
            (faults["fault_type"] == "missing_readings")
        ]

        for _, fault in nearby.iterrows():
            distance = min(
                abs((alert["start_time"] - fault["end_time"]).total_seconds()),
                abs((fault["start_time"] - alert["end_time"]).total_seconds())
            )

            if distance <= 24 * 3600:
                remaining.loc[i, "attribution"] = (
                    "possible_secondary_missing_effect"
                )
                break

    remaining_links = pd.DataFrame({
        "fault_id": None,
        "alert_id": remaining["alert_id"],
        "fault_type": None,
        "alert_type": remaining["alert_type"],
        "baseline_overlap": remaining["baseline_overlap"],
        "attribution": remaining["attribution"]
    })

    all_links = pd.concat(
        [link_report, remaining_links],
        ignore_index=True
    )

    fault_report.to_csv(FAULT_REPORT, index=False)
    all_links.to_csv(ALERT_REPORT, index=False)

    print("\n========== EVENT-LEVEL EVALUATION ==========")
    print("Injected faults:", len(faults))
    print("Detected faults:", int(fault_report["detected"].sum()))
    print("Missed faults:", int((~fault_report["detected"]).sum()))

    print("\nFault detection by type:")
    for kind, group in fault_report.groupby("fault_type"):
        count = int(group["detected"].sum())
        print(f"{kind}: {count}/{len(group)}")

    print("\n========== ALERT ATTRIBUTION ==========")
    print("Total generated alerts:", len(alerts))
    print("Alerts assigned to injected faults:", len(link_report))
    print("Remaining alerts:", len(remaining))

    print("\nRemaining alert categories:")
    print(remaining["attribution"].value_counts().to_string())

    print("\nBaseline-overlapping alerts:", int(
        alerts["baseline_overlap"].sum()
    ))

    print("\nSaved fault report:", FAULT_REPORT)
    print("Saved alert report:", ALERT_REPORT)


if __name__ == "__main__":
    main()
