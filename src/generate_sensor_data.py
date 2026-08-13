from pathlib import Path
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = PROJECT_ROOT / "data" / "raw" / "observations.csv"


def generate_sensor_data():
    timestamps = pd.date_range(
        start="2026-08-08 00:00",
        periods=72,
        freq="h"
    )

    rng = np.random.default_rng(42)

    rainfall = rng.uniform(0, 5, 72)

    # Simulated rainfall event
    rainfall[30:42] += np.linspace(5, 35, 12)
    rainfall[42:48] += np.linspace(30, 5, 6)

    lake_level = np.zeros(72)
    river_level = np.zeros(72)

    lake_level[0] = 3.20
    river_level[0] = 2.10

    for i in range(1, 72):
        lake_level[i] = (
            lake_level[i - 1]
            + rainfall[i] * 0.003
            + rng.normal(0, 0.005)
        )

        river_level[i] = (
            river_level[i - 1]
            + rainfall[i] * 0.006
            + rng.normal(0, 0.008)
        )

    df = pd.DataFrame({
        "timestamp": timestamps,
        "station_id": "THULAGI_DEMO_01",
        "station_type": "lake",
        "lake_level_m": lake_level.round(3),
        "river_level_m": river_level.round(3),
        "rainfall_mm": rainfall.round(2)
    })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"Created: {OUTPUT_FILE}")
    print(f"Records: {len(df)}")


if __name__ == "__main__":
    generate_sensor_data()