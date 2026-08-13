from pathlib import Path
import pandas as pd

INPUT = Path("data/water_level/simulated_water_level.csv")
OUTPUT = Path("data/water_level/water_level_indicators.csv")

print("THULAGI WATER-LEVEL TELEMETRY ANALYSIS")
print("-" * 50)

df = pd.read_csv(INPUT, parse_dates=["timestamp"])

# 10-minute rate -> m/hour
df["rise_rate_m_per_hour"] = df["level_change_m"] * 6

# 1-hour rolling mean rate
df["rate_1h_m_per_hour"] = (
    df["rise_rate_m_per_hour"]
    .rolling(6, min_periods=6)
    .mean()
)

# 1-hour smoothed acceleration
df["acceleration_m_per_hour2"] = (
    df["rate_1h_m_per_hour"].diff(6)
)

# 10-hour change
df["change_10h_m"] = (
    df["water_level_m"] -
    df["water_level_m"].shift(60)
)

# 10-hour mean rate
df["mean_rate_10h_m_per_hour"] = (
    df["change_10h_m"] / 10
)

# Trend
def classify_trend(rate):
    if pd.isna(rate):
        return "UNKNOWN"
    if rate > 0.01:
        return "RISING"
    if rate < -0.01:
        return "FALLING"
    return "STABLE"

df["trend"] = df["rate_1h_m_per_hour"].apply(classify_trend)

# Latest complete record
latest = df.dropna(
    subset=[
        "change_10h_m",
        "rate_1h_m_per_hour",
        "acceleration_m_per_hour2"
    ]
).iloc[-1]

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT, index=False)

print(f"Records:                 {len(df)}")
print(f"Latest timestamp:        {latest['timestamp']}")
print(f"Current level:           {latest['water_level_m']:.2f} m")
print(f"10-hour change:          {latest['change_10h_m']:+.3f} m")
print(f"Mean 10-hour rate:       {latest['mean_rate_10h_m_per_hour']:+.3f} m/hour")
print(f"1-hour smoothed rate:    {latest['rate_1h_m_per_hour']:+.3f} m/hour")
print(f"Acceleration:            {latest['acceleration_m_per_hour2']:+.3f} m/hour²")
print(f"Trend:                   {latest['trend']}")
print()
print("IMPORTANT: WATER LEVEL IS SIMULATED")
print(f"Saved: {OUTPUT}")