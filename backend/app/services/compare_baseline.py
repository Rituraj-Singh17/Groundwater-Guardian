from pathlib import Path
import pandas as pd

from app.services.detection import detect_anomalies

BASELINE = Path("../datasets/processed/detection_results.csv")
SIMULATED = Path("../datasets/processed/simulated_fault_data.csv")
OUTPUT = Path("../datasets/processed/baseline_comparison.csv")
NEW_ALERTS = Path("../datasets/processed/new_simulated_alerts.csv")

TIME = "Data Acquisition Time"
LEVEL = "Groundwater Level Telemetry 6 Hourly (meter)"


def main():
    baseline = pd.read_csv(BASELINE)
    baseline["start_time"] = pd.to_datetime(baseline["start_time"])
    baseline["end_time"] = pd.to_datetime(baseline["end_time"])

    df = pd.read_csv(SIMULATED, low_memory=False)
    data = pd.DataFrame({
        "station_id": df["station_id"],
        "observed_at": pd.to_datetime(df[TIME], errors="coerce"),
        "groundwater_level_m": pd.to_numeric(
            df[LEVEL], errors="coerce"
        )
    })

    simulated = pd.DataFrame(detect_anomalies(data))

    if simulated.empty:
        print("No simulated alerts found.")
        return

    simulated["start_time"] = pd.to_datetime(
        simulated["start_time"]
    )
    simulated["end_time"] = pd.to_datetime(
        simulated["end_time"]
    )

    baseline_groups = {
        (str(station), kind): group
        for (station, kind), group in baseline.groupby(
            ["station_id", "alert_type"]
        )
    }

    matched_baseline = []
    new_alerts = []

    for index, alert in simulated.iterrows():
        key = (str(alert["station_id"]), alert["alert_type"])
        candidates = baseline_groups.get(key)

        matched = False

        if candidates is not None:
            matched = (
                (candidates["start_time"] <= alert["end_time"]) &
                (candidates["end_time"] >= alert["start_time"])
            ).any()

        if matched:
            matched_baseline.append(index)
        else:
            new_alerts.append(index)

    simulated["baseline_match"] = simulated.index.isin(
        matched_baseline
    )
    simulated["new_alert"] = ~simulated["baseline_match"]

    simulated.to_csv(OUTPUT, index=False)
    simulated.loc[new_alerts].to_csv(NEW_ALERTS, index=False)

    print("\n========== BASELINE COMPARISON ==========")
    print("Original alerts:", len(baseline))
    print("Simulated alerts:", len(simulated))
    print("Matched to baseline:", len(matched_baseline))
    print("New unmatched alerts:", len(new_alerts))

    print("\nNew alerts by type:")
    if new_alerts:
        print(
            simulated.loc[new_alerts, "alert_type"]
            .value_counts().to_string()
        )

    print("\nSaved comparison:", OUTPUT)
    print("Saved new alerts:", NEW_ALERTS)


if __name__ == "__main__":
    main()
