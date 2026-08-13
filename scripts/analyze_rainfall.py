from pathlib import Path
import pandas as pd
import numpy as np

# --------------------------------------------------
# THULAGI LAKE RAINFALL ANALYSIS
# --------------------------------------------------

INPUT = Path("data/rainfall/rainfall_daily.csv")
OUTPUT = Path("data/rainfall/rainfall_indicators.csv")

print("THULAGI RAINFALL ANALYSIS")
print("-" * 40)

# Load data
df = pd.read_csv(INPUT, parse_dates=["date"])

# Ensure numeric rainfall
df["rainfall_mm"] = pd.to_numeric(df["rainfall_mm"], errors="coerce")

# Do NOT treat missing rainfall as zero
df["rainfall_3day_mm"] = df["rainfall_mm"].rolling(3, min_periods=3).sum()
df["rainfall_7day_mm"] = df["rainfall_mm"].rolling(7, min_periods=7).sum()

# --------------------------------------------------
# Historical baseline
# Use complete years 2001-2025
# --------------------------------------------------

historical = df[
    (df["date"].dt.year >= 2001) &
    (df["date"].dt.year <= 2025)
].copy()

# Historical 7-day rainfall distribution
historical_7day = historical["rainfall_7day_mm"].dropna()

# Latest date with complete 7-day rainfall
current = df.dropna(subset=["rainfall_7day_mm"]).iloc[-1]

current_date = current["date"]
current_daily = current["rainfall_mm"]
current_3day = current["rainfall_3day_mm"]
current_7day = current["rainfall_7day_mm"]

# --------------------------------------------------
# Empirical percentile
# --------------------------------------------------

percentile = (
    (historical_7day <= current_7day).sum()
    / len(historical_7day)
) * 100

# --------------------------------------------------
# Prototype rainfall evidence category
# These are evidence categories, NOT operational
# warning thresholds.
# --------------------------------------------------

if percentile >= 95:
    status = "HIGH"
elif percentile >= 75:
    status = "ELEVATED"
else:
    status = "NORMAL"

# --------------------------------------------------
# Save indicators
# --------------------------------------------------

result = pd.DataFrame([{
    "date": current_date,
    "daily_rainfall_mm": current_daily,
    "rainfall_3day_mm": current_3day,
    "rainfall_7day_mm": current_7day,
    "historical_7day_percentile": percentile,
    "rainfall_status": status
}])

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
result.to_csv(OUTPUT, index=False)

# --------------------------------------------------
# Display result
# --------------------------------------------------

print(f"Latest complete rainfall date: {current_date.date()}")
print(f"Daily rainfall:                {current_daily:.2f} mm")
print(f"3-day rainfall:                {current_3day:.2f} mm")
print(f"7-day rainfall:                {current_7day:.2f} mm")
print(f"Historical percentile:         {percentile:.2f}")
print(f"Rainfall evidence:             {status}")
print()
print(f"Saved: {OUTPUT}")