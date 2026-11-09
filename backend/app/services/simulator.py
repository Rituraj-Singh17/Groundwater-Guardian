from pathlib import Path
import numpy as np
import pandas as pd

SOURCE = Path("../datasets/processed/maha_validated.csv")
OUTPUT = Path("../datasets/processed/simulated_fault_data.csv")
LABELS = Path("../datasets/processed/simulation_ground_truth.csv")

SEED = 42
FAULTS_PER_TYPE = 20
LEVEL = "Groundwater Level Telemetry 6 Hourly (meter)"
TIME = "Data Acquisition Time"


def main():
    rng = np.random.default_rng(SEED)

    df = pd.read_csv(SOURCE, low_memory=False)
    df[TIME] = pd.to_datetime(df[TIME], errors="coerce")
    df[LEVEL] = pd.to_numeric(df[LEVEL], errors="coerce")
    df = df.dropna(subset=["station_id", TIME, LEVEL])
    df = df.sort_values(["station_id", TIME]).reset_index(drop=True)

    used = set()
    labels = []

    def choose_window(size, min_span=0):
        groups = [
            (station, group.index.to_numpy(),
             group[TIME].to_numpy())
            for station, group in df.groupby("station_id")
            if len(group) >= size
        ]

        for _ in range(10000):
            station, indexes, times = groups[
                int(rng.integers(len(groups)))
            ]

            start = int(rng.integers(len(indexes) - size + 1))
            window = indexes[start:start + size]

            if any(i in used for i in window):
                continue

            selected_times = times[start:start + size]
            gaps = np.diff(selected_times).astype(
                "timedelta64[m]"
            ).astype(int)

            if len(gaps) and not np.all((gaps >= 330) & (gaps <= 390)):
                continue

            span = (
                selected_times[-1] - selected_times[0]
            ) / np.timedelta64(1, "h")

            if span >= min_span:
                return station, window, selected_times

        raise RuntimeError(
            f"Could not find a valid window of size {size}"
        )

    # Missing readings
    for n in range(FAULTS_PER_TYPE):
        station, window, times = choose_window(5)
        middle = window[1:4]

        labels.append({
            "fault_id": f"MISSING-{n+1}",
            "fault_type": "missing_readings",
            "station_id": station,
            "start_time": times[1],
            "end_time": times[3]
        })

        used.update(window)
        df = df.drop(index=middle)

    # Flatlines
    for n in range(FAULTS_PER_TYPE):
        station, window, times = choose_window(6, 30)
        value = float(df.loc[window[0], LEVEL])

        df.loc[window, LEVEL] = value

        labels.append({
            "fault_id": f"FLATLINE-{n+1}",
            "fault_type": "flatline",
            "station_id": station,
            "start_time": times[0],
            "end_time": times[-1]
        })

        used.update(window)

    # Sudden spikes
    for n in range(FAULTS_PER_TYPE):
        station, window, times = choose_window(3)
        target = window[1]
        original = float(df.loc[target, LEVEL])
        injected = original + (100 if n % 2 == 0 else -100)

        df.loc[target, LEVEL] = injected

        labels.append({
            "fault_id": f"SPIKE-{n+1}",
            "fault_type": "sudden_change",
            "station_id": station,
            "start_time": times[0],
            "end_time": times[1],
            "original_value": original,
            "injected_value": injected
        })

        used.update(window)

    df.to_csv(OUTPUT, index=False)
    pd.DataFrame(labels).to_csv(LABELS, index=False)

    print("\n========== SIMULATION COMPLETE ==========")
    print("Missing faults:", FAULTS_PER_TYPE)
    print("Flatline faults:", FAULTS_PER_TYPE)
    print("Sudden spikes:", FAULTS_PER_TYPE)
    print("Total injected faults:", len(labels))
    print("Simulated rows:", len(df))
    print("Ground-truth labels:", len(labels))
    print("Dataset:", OUTPUT)
    print("Labels:", LABELS)


if __name__ == "__main__":
    main()
