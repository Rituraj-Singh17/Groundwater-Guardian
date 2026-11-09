from pathlib import Path
import pandas as pd
from app.services.detection import detect_anomalies

path = Path("../datasets/processed/maha_validated.csv")
df = pd.read_csv(path)

data = pd.DataFrame({
    "station_id": df["station_id"],
    "observed_at": df["Data Acquisition Time"],
    "groundwater_level_m": df[
        "Groundwater Level Telemetry 6 Hourly (meter)"
    ]
})

alerts = detect_anomalies(data)
result = pd.DataFrame(alerts)

print("\n========== ANOMALY DETECTION RESULTS ==========")
print("Total alerts:", len(alerts))

if not result.empty:
    print("\nAlerts by type:")
    print(result["alert_type"].value_counts().to_string())

    print("\nAlerts by severity:")
    print(result["severity"].value_counts().to_string())

    print("\nSample alerts:")
    print(result.head(15).to_string(index=False))

    output = Path("../datasets/processed/detection_results.csv")
    result.to_csv(output, index=False)
    print("\nSaved results to:", output)
else:
    print("No anomalies detected.")
