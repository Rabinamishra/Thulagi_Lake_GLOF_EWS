from pathlib import Path
import pandas as pd


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "observations.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "derived_variables.csv"


# ---------------------------------------------------------
# Prototype thresholds
# ---------------------------------------------------------
# IMPORTANT:
# These are illustrative thresholds for this demonstration.
# They are NOT official DHM, UNDP, or project warning thresholds.
# ---------------------------------------------------------

RAIN_1HR_WATCH = 20
RAIN_3HR_WATCH = 40
RAIN_6HR_WATCH = 60
RAIN_24HR_WATCH = 100

LAKE_RATE_WATCH = 0.15
RIVER_RATE_WATCH = 0.10


# ---------------------------------------------------------
# Calculate derived hydrometeorological variables
# ---------------------------------------------------------

def calculate_variables(df):

    # Convert timestamp to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Sort observations chronologically
    df = df.sort_values("timestamp").reset_index(drop=True)

    # -----------------------------------------------------
    # Rainfall accumulation
    # -----------------------------------------------------

    df["rainfall_1hr_mm"] = (
        df["rainfall_mm"]
        .rolling(window=1)
        .sum()
    )

    df["rainfall_3hr_mm"] = (
        df["rainfall_mm"]
        .rolling(window=3)
        .sum()
    )

    df["rainfall_6hr_mm"] = (
        df["rainfall_mm"]
        .rolling(window=6)
        .sum()
    )

    df["rainfall_24hr_mm"] = (
        df["rainfall_mm"]
        .rolling(window=24)
        .sum()
    )

    # -----------------------------------------------------
    # Lake-level rate of change
    # -----------------------------------------------------

    df["lake_rate_1hr_m_hr"] = (
        df["lake_level_m"].diff()
    )

    df["lake_rate_3hr_m_hr"] = (
        df["lake_level_m"].diff(periods=3) / 3
    )

    df["lake_rate_6hr_m_hr"] = (
        df["lake_level_m"].diff(periods=6) / 6
    )

    # -----------------------------------------------------
    # River-level rate of change
    # -----------------------------------------------------

    df["river_rate_1hr_m_hr"] = (
        df["river_level_m"].diff()
    )

    df["river_rate_3hr_m_hr"] = (
        df["river_level_m"].diff(periods=3) / 3
    )

    df["river_rate_6hr_m_hr"] = (
        df["river_level_m"].diff(periods=6) / 6
    )

    return df


# ---------------------------------------------------------
# Determine alert level
# ---------------------------------------------------------

def determine_alert(row):

    triggered = []

    # -----------------------------------------------------
    # Rainfall thresholds
    # -----------------------------------------------------

    if row["rainfall_1hr_mm"] >= RAIN_1HR_WATCH:
        triggered.append(
            f"1-hour rainfall {row['rainfall_1hr_mm']:.1f} mm"
        )

    if row["rainfall_3hr_mm"] >= RAIN_3HR_WATCH:
        triggered.append(
            f"3-hour rainfall {row['rainfall_3hr_mm']:.1f} mm"
        )

    if row["rainfall_6hr_mm"] >= RAIN_6HR_WATCH:
        triggered.append(
            f"6-hour rainfall {row['rainfall_6hr_mm']:.1f} mm"
        )

    if row["rainfall_24hr_mm"] >= RAIN_24HR_WATCH:
        triggered.append(
            f"24-hour rainfall {row['rainfall_24hr_mm']:.1f} mm"
        )

    # -----------------------------------------------------
    # Lake-level change
    # -----------------------------------------------------

    if row["lake_rate_1hr_m_hr"] >= LAKE_RATE_WATCH:
        triggered.append(
            f"lake-level rise "
            f"{row['lake_rate_1hr_m_hr']:.3f} m/hr"
        )

    # -----------------------------------------------------
    # River-level change
    # -----------------------------------------------------

    if row["river_rate_1hr_m_hr"] >= RIVER_RATE_WATCH:
        triggered.append(
            f"river-level rise "
            f"{row['river_rate_1hr_m_hr']:.3f} m/hr"
        )

    # -----------------------------------------------------
    # Alert classification
    # -----------------------------------------------------
    #
    # 0 triggered conditions  -> NORMAL
    # 1 triggered condition   -> WATCH
    # 2+ conditions           -> WARNING
    #
    # This is a prototype decision rule.
    # -----------------------------------------------------

    if len(triggered) >= 2:
        alert = "WARNING"

    elif len(triggered) == 1:
        alert = "WATCH"

    else:
        alert = "NORMAL"

    # Create human-readable explanation
    reason = "; ".join(triggered)

    if not reason:
        reason = "No prototype threshold exceeded"

    return pd.Series({
        "alert_level": alert,
        "alert_reason": reason
    })


# ---------------------------------------------------------
# Main processing workflow
# ---------------------------------------------------------

def main():

    print("Loading observation data...")

    # Check that input exists
    if not INPUT_FILE.exists():
        print()
        print("ERROR: Input file not found.")
        print(f"Expected file: {INPUT_FILE}")
        return

    # Read observation data
    df = pd.read_csv(INPUT_FILE)

    print(f"Loaded {len(df)} observations.")

    # Calculate derived variables
    df = calculate_variables(df)

    # Determine alert levels and reasons
    alert_results = df.apply(
        determine_alert,
        axis=1
    )

    # Add results to dataframe
    df["alert_level"] = alert_results["alert_level"]
    df["alert_reason"] = alert_results["alert_reason"]

    # -----------------------------------------------------
    # Save processed data
    # -----------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print("Alert processing complete.")
    print(f"Output: {OUTPUT_FILE}")

    # -----------------------------------------------------
    # Display summary
    # -----------------------------------------------------

    print()
    print("Alert summary:")
    print(
        df["alert_level"]
        .value_counts()
    )

    # -----------------------------------------------------
    # Display latest observation
    # -----------------------------------------------------

    latest = df.iloc[-1]

    print()
    print("Latest observation:")
    print(f"Time: {latest['timestamp']}")
    print(f"Lake level: {latest['lake_level_m']:.3f} m")
    print(f"River level: {latest['river_level_m']:.3f} m")
    print(f"Rainfall: {latest['rainfall_mm']:.2f} mm")
    print(f"Alert: {latest['alert_level']}")
    print(f"Reason: {latest['alert_reason']}")


# ---------------------------------------------------------
# Run program
# ---------------------------------------------------------

if __name__ == "__main__":
    main()