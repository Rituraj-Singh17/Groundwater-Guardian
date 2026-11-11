from pathlib import Path
import pandas as pd

from app.services.detection import detect_anomalies

DATA = Path("../datasets/processed/simulated_fault_data.csv")
LABELS = Path("../datasets/processed/simulation_ground_truth.csv")
OUTPUT = Path("../datasets/processed/simulation_evaluation.csv")

TIME = "Data Acquisition Time"
LEVEL = "Groundwater Level Telemetry 6 Hourly (meter)"


def main():
    df = pd.read_csv(DATA, low_memory=False)
    labels = pd.read_csv(LABELS)

    df[TIME] = pd.to_datetime(df[TIME], errors="coerce")
    df[LEVEL] = pd.to_numeric(df[LEVEL], errors="coerce")

    data = pd.DataFrame({
        "station_id": df["station_id"],
        "observed_at": df[TIME],
        "groundwater_level_m": df[LEVEL]
    })

    alerts = pd.DataFrame(detect_anomalies(data))

    if alerts.empty:
        print("No alerts detected.")
        return

    alerts["start_time"] = pd.to_datetime(alerts["start_time"])
    alerts["end_time"] = pd.to_datetime(alerts["end_time"])
    labels["start_time"] = pd.to_datetime(labels["start_time"])
    labels["end_time"] = pd.to_datetime(labels["end_time"])

    used_alerts = set()
    results = []

    for _, fault in labels.iterrows():
        expected_type = fault["fault_type"]

        candidates = alerts[
            (alerts["station_id"].astype(str) ==
             str(fault["station_id"])) &
            (alerts["alert_type"] == expected_type) &
            (alerts["start_time"] <= fault["end_time"]) &
            (alerts["end_time"] >= fault["start_time"])
        ]

        available = candidates[
            ~candidates.index.isin(used_alerts)
        ]

        detected = not available.empty

        if detected:
            alert_index = available.index[0]
            used_alerts.add(alert_index)
        else:
            alert_index = None

        results.append({
            "fault_id": fault["fault_id"],
            "fault_type": expected_type,
            "station_id": fault["station_id"],
            "detected": detected,
            "matched_alert_type": (
                alerts.loc[alert_index, "alert_type"]
                if detected else None
            )
        })

    result = pd.DataFrame(results)
    result.to_csv(OUTPUT, index=False)

    print("\n========== SIMULATION EVALUATION ==========")
    print("Injected faults:", len(labels))
    print("Detected faults:", int(result["detected"].sum()))
    print("Missed faults:", int((~result["detected"]).sum()))

    recall = result["detected"].mean() * 100
    print(f"\nOverall fault detection recall: {recall:.2f}%")

    print("\n========== RESULTS BY FAULT TYPE ==========")

    for fault_type, group in result.groupby("fault_type"):
        detected = int(group["detected"].sum())
        total = len(group)
        percentage = detected / total * 100

        print(
            f"{fault_type}: {detected}/{total} "
            f"detected ({percentage:.2f}%)"
        )

    print("\n========== ALERT SUMMARY ==========")
    print("Total alerts generated:", len(alerts))
    print("\nAlerts by type:")
    print(alerts["alert_type"].value_counts().to_string())

    print("\nDetailed evaluation saved to:", OUTPUT)


if __name__ == "__main__":
    main()
