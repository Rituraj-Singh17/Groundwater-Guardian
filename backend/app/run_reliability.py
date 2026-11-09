from pathlib import Path
import pandas as pd

from app.database import Base, engine, SessionLocal
from app import models
from app.services.reliability import score_stations
from app.services.explainability import explain_station_scores
from app.services.reliability_repository import save_reliability_scores

ROOT = Path("../datasets/processed")
SOURCE = ROOT / "maha_validated.csv"
ALERTS = ROOT / "detection_results.csv"
OUTPUT = ROOT / "station_reliability_scores.csv"

LEVEL = "Groundwater Level Telemetry 6 Hourly (meter)"
TIME = "Data Acquisition Time"


def main():
    df = pd.read_csv(SOURCE, low_memory=False)
    alerts = pd.read_csv(ALERTS, low_memory=False)

    observations = pd.DataFrame({
        "station_id": df["station_id"],
        "observed_at": df[TIME],
        "groundwater_level_m": df[LEVEL]
    })

    scores = score_stations(observations, alerts)
    scores = explain_station_scores(scores)

    # Preserve the CSV output as an audit/export artifact.
    scores.to_csv(OUTPUT, index=False)

    # Create only missing tables; existing tables are not dropped.
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        result = save_reliability_scores(db, scores)
    finally:
        db.close()

    print("\n========== EXPLAINABLE RELIABILITY RESULTS ==========")
    print("Stations evaluated:", len(scores))

    print("\nReliability categories:")
    print(scores["reliability_category"].value_counts().to_string())

    print("\nInvestigation priorities:")
    print(scores["investigation_priority"].value_counts().to_string())

    print("\nDatabase persistence:")
    print("New records:", result["inserted"])
    print("Updated records:", result["updated"])

    print("\nCSV saved:", OUTPUT)


if __name__ == "__main__":
    main()
