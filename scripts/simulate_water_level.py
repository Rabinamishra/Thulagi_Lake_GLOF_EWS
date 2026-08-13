from pathlib import Path
import pandas as pd
import numpy as np

# --------------------------------------------------
# THULAGI LAKE SIMULATED WATER-LEVEL TELEMETRY
# --------------------------------------------------

OUTPUT = Path("data/water_level/simulated_water_level.csv")

np.random.seed(42)

# Simulate the last 24 hours at 10-minute intervals
timestamps = pd.date_range(
    end="2026-08-09 18:00:00",
    periods=145,
    freq="10min"
)

# Baseline water level
base_level = 22.40

# Gradual rise + stronger rise near the end
trend = np.linspace(0, 0.65, len(timestamps))

# Small sensor-like variation
noise = np.random.normal(0, 0.015, len(timestamps))

water_level = base_level + trend + noise

df = pd.DataFrame({
    "timestamp": timestamps,
    "water_level_m": water_level
})

# Calculate change over each 10-minute interval
df["level_change_m"] = df["water_level_m"].diff()

# Convert to rate in m/hour
df["rise_rate_m_per_hour"] = (
    df["level_change_m"] * 6
)

# Simulated sensor status
df["sensor_status"] = "SIMULATED"

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT, index=False)

print("THULAGI SIMULATED WATER-LEVEL TELEMETRY")
print("-" * 45)
print(f"Records: {len(df)}")
print(f"Starting level: {df['water_level_m'].iloc[0]:.2f} m")
print(f"Latest level:   {df['water_level_m'].iloc[-1]:.2f} m")
print(f"Latest rise rate: {df['rise_rate_m_per_hour'].iloc[-1]:.3f} m/hour")
print()
print(f"Saved: {OUTPUT}")