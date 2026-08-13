import sys
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox
from pathlib import Path

# ------------------------------------------------------------
# THULAGI LAKE GLOF EWS - PROTOTYPE USER INTERFACE
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from alert_engine import (
    RainfallInput,
    LakeAreaInput,
    SimulatedWaterLevelInput,
    run_alert_engine,
    demo_operational_extension,
)


# ============================================================
# WINDOW
# ============================================================

root = tk.Tk()
root.title("Thulagi Lake GLOF EWS Prototype")
root.geometry("800x850")

main = ttk.Frame(root, padding=20)
main.pack(fill="both", expand=True)


# ============================================================
# TITLE
# ============================================================

ttk.Label(
    main,
    text="THULAGI LAKE GLOF Early Warning System",
    font=("Segoe UI", 20, "bold"),
).pack(anchor="w")

ttk.Label(
    main,
    text="Prototype Decision-Support Interface",
    font=("Segoe UI", 11),
).pack(anchor="w", pady=(0, 8))

ttk.Label(
    main,
    text="PROTOTYPE",
    font=("Segoe UI", 10, "bold"),
).pack(anchor="w", pady=(0, 12))


# ============================================================
# INPUT STORAGE
# ============================================================

entries = {}


def add_section(title):
    ttk.Label(
        main,
        text=title,
        font=("Segoe UI", 13, "bold"),
    ).pack(anchor="w", pady=(12, 5))


def add_input(label, key, default=""):
    row = ttk.Frame(main)
    row.pack(fill="x", pady=3)

    ttk.Label(
        row,
        text=label,
        width=40,
    ).pack(side="left")

    entry = ttk.Entry(row, width=25)
    entry.insert(0, default)
    entry.pack(side="left")

    entries[key] = entry


def get_float(key):
    return float(entries[key].get().strip())


# ============================================================
# 1. RAINFALL
# ============================================================

add_section("1. REAL RAINFALL")

add_input(
    "Daily rainfall (mm):",
    "daily",
    "10.47",
)

add_input(
    "3-day rainfall (mm):",
    "rain3",
    "46.50",
)

add_input(
    "7-day rainfall (mm):",
    "rain7",
    "132.45",
)

add_input(
    "Historical 7-day percentile (0–100):",
    "percentile",
    "97.84",
)


# ============================================================
# 2. SATELLITE LAKE AREA
# ============================================================

add_section("2. SATELLITE LAKE AREA")

add_input(
    "Latest lake area (km²):",
    "latest_area",
    "0.9291",
)

add_input(
    "Previous lake area (km²):",
    "previous_area",
    "0.9167",
)

add_input(
    "Years between observations:",
    "years",
    "1",
)


# ============================================================
# 3. WATER-LEVEL TELEMETRY
# ============================================================

add_section("3. WATER-LEVEL TELEMETRY")

ttk.Label(
    main,
    text=(
        "Enter the number of observations. "
        "The system will calculate rate, trend and acceleration automatically."
    ),
    wraplength=700,
).pack(anchor="w", pady=(0, 5))


water_count_frame = ttk.Frame(main)
water_count_frame.pack(fill="x", pady=3)

ttk.Label(
    water_count_frame,
    text="Number of observations:",
    width=40,
).pack(side="left")

water_count_entry = ttk.Entry(
    water_count_frame,
    width=25,
)

water_count_entry.insert(0, "5")
water_count_entry.pack(side="left")


water_input_frame = ttk.Frame(main)
water_input_frame.pack(fill="x", pady=5)


water_entries = []


def create_water_level_inputs():
    """Create date/time and water-level fields."""

    for widget in water_input_frame.winfo_children():
        widget.destroy()

    water_entries.clear()

    try:
        count = int(water_count_entry.get().strip())

        if count < 2:
            raise ValueError

    except ValueError:
        messagebox.showerror(
            "Invalid Input",
            "Enter a whole number of observations (minimum 2).",
        )
        return

    ttk.Label(
        water_input_frame,
        text="Observation",
        width=12,
        font=("Segoe UI", 9, "bold"),
    ).grid(row=0, column=0, padx=3, pady=2)

    ttk.Label(
        water_input_frame,
        text="Date/time (YYYY-MM-DD HH:MM)",
        width=28,
        font=("Segoe UI", 9, "bold"),
    ).grid(row=0, column=1, padx=3, pady=2)

    ttk.Label(
        water_input_frame,
        text="Water level (m)",
        width=18,
        font=("Segoe UI", 9, "bold"),
    ).grid(row=0, column=2, padx=3, pady=2)

    for i in range(count):

        ttk.Label(
            water_input_frame,
            text=str(i + 1),
            width=12,
        ).grid(row=i + 1, column=0, padx=3, pady=2)

        date_entry = ttk.Entry(
            water_input_frame,
            width=28,
        )

        date_entry.grid(
            row=i + 1,
            column=1,
            padx=3,
            pady=2,
        )

        level_entry = ttk.Entry(
            water_input_frame,
            width=18,
        )

        level_entry.grid(
            row=i + 1,
            column=2,
            padx=3,
            pady=2,
        )

        water_entries.append(
            (date_entry, level_entry)
        )


ttk.Button(
    water_count_frame,
    text="CREATE INPUTS",
    command=create_water_level_inputs,
).pack(side="left", padx=8)


# Create default five observation rows
create_water_level_inputs()


# ============================================================
# RESULT
# ============================================================

result_frame = ttk.LabelFrame(
    main,
    text="ALERT RESULT",
    padding=15,
)

result_frame.pack(
    fill="both",
    expand=True,
    pady=(15, 10),
)

alert_label = ttk.Label(
    result_frame,
    text="Enter data and click CALCULATE ALERT",
    font=("Segoe UI", 18, "bold"),
)

alert_label.pack(anchor="w")

score_label = ttk.Label(
    result_frame,
    text="",
    font=("Segoe UI", 12),
)

score_label.pack(anchor="w", pady=(5, 8))

details_label = ttk.Label(
    result_frame,
    text="",
    justify="left",
    wraplength=700,
)

details_label.pack(anchor="w")


# ============================================================
# WATER-LEVEL CALCULATION
# ============================================================

def calculate_water_level():

    observations = []

    for date_entry, level_entry in water_entries:

        date_text = date_entry.get().strip()
        level_text = level_entry.get().strip()

        if not date_text or not level_text:
            raise ValueError(
                "Please enter all water-level observations."
            )

        timestamp = datetime.strptime(
            date_text,
            "%Y-%m-%d %H:%M",
        )

        level = float(level_text)

        observations.append(
            (timestamp, level)
        )

    # Sort chronologically
    observations.sort(
        key=lambda x: x[0]
    )

    if len(observations) < 2:
        raise ValueError(
            "At least two water-level observations are required."
        )

    # --------------------------------------------------------
    # Latest rate
    # --------------------------------------------------------

    latest_time, latest_level = observations[-1]
    previous_time, previous_level = observations[-2]

    latest_dt_hours = (
        latest_time - previous_time
    ).total_seconds() / 3600

    if latest_dt_hours <= 0:
        raise ValueError(
            "Water-level observations must have different "
            "and increasing times."
        )

    latest_rate = (
        latest_level - previous_level
    ) / latest_dt_hours

    # --------------------------------------------------------
    # Trend
    # --------------------------------------------------------

    if latest_rate > 0:
        trend = "RISING"
    elif latest_rate < 0:
        trend = "FALLING"
    else:
        trend = "STABLE"

    # --------------------------------------------------------
    # Acceleration
    # --------------------------------------------------------

    if len(observations) >= 3:

        time_3, level_3 = observations[-3]
        time_2, level_2 = observations[-2]

        previous_dt_hours = (
            time_2 - time_3
        ).total_seconds() / 3600

        if previous_dt_hours <= 0:
            raise ValueError(
                "Water-level observations must be "
                "chronologically ordered."
            )

        previous_rate = (
            level_2 - level_3
        ) / previous_dt_hours

        acceleration = (
            latest_rate - previous_rate
        ) / latest_dt_hours

    else:
        acceleration = 0.0

    # --------------------------------------------------------
    # 10-hour equivalent change
    # --------------------------------------------------------

    change_10hr = latest_rate * 10

    return SimulatedWaterLevelInput(
        current_level_m=latest_level,
        change_10hr_m=change_10hr,
        latest_rate_m_per_hr=latest_rate,
        latest_acceleration_m_per_hr2=acceleration,
        trend=trend,
    )


# ============================================================
# CALCULATION
# ============================================================

def calculate():

    try:

        # ----------------------------------------------------
        # Rainfall
        # ----------------------------------------------------

        rainfall = RainfallInput(
            daily_mm=get_float("daily"),
            rainfall_3day_mm=get_float("rain3"),
            rainfall_7day_mm=get_float("rain7"),
            historical_7day_percentile=get_float(
                "percentile"
            ),
        )

        # ----------------------------------------------------
        # Lake
        # ----------------------------------------------------

        lake = LakeAreaInput(
            latest_area_km2=get_float(
                "latest_area"
            ),
            previous_area_km2=get_float(
                "previous_area"
            ),
            years_between_observations=get_float(
                "years"
            ),
        )

        # ----------------------------------------------------
        # Water level
        # ----------------------------------------------------

        water = calculate_water_level()

        # ----------------------------------------------------
        # Run alert engine
        # ----------------------------------------------------

        result = run_alert_engine(
            rainfall,
            lake,
            water,
        )

        # ----------------------------------------------------
        # Water-level extension
        # ----------------------------------------------------

        demo = demo_operational_extension(
            result,
            water,
        )

        # ----------------------------------------------------
        # Lake change
        # ----------------------------------------------------

        lake_change = (
            (
                lake.latest_area_km2
                - lake.previous_area_km2
            )
            / lake.previous_area_km2
        ) * 100

        # ----------------------------------------------------
        # Main result
        # ----------------------------------------------------

        alert_label.config(
            text=f"PROTOTYPE: {result.level}"
        )

        score_label.config(
            text=(
                f"Prototype score: "
                f"{result.score}/{result.max_score}"
            )
        )

        # ----------------------------------------------------
        # Details
        # ----------------------------------------------------

        details = (
            f"RAINFALL\n"
            f"  Score: {result.rainfall_score}/2\n"
            f"  Status: {result.rainfall_status}\n\n"

            f"LAKE AREA\n"
            f"  Score: {result.lake_growth_score}/2\n"
            f"  Status: {result.lake_growth_status}\n"
            f"  Latest change: {lake_change:+.2f}%\n\n"

            f"WATER-LEVEL TELEMETRY\n"
            f"  Current level: "
            f"{water.current_level_m:.2f} m\n"
            f"  Rate of change: "
            f"{water.latest_rate_m_per_hr:+.3f} m/hour\n"
            f"  Trend: {water.trend}\n"
            f"  Acceleration: "
            f"{water.latest_acceleration_m_per_hr2:+.3f} "
            f"m/hour²\n\n"

            f"WATER-LEVEL EXTENSION\n"
            f"  Hypothetical score: "
            f"{demo.hypothetical_score}/"
            f"{demo.hypothetical_max}\n"
            f"  Hypothetical level: "
            f"{demo.hypothetical_level}\n"
            f"  Water-level contribution: "
            f"{demo.water_level_score}/2 — "
            f"{demo.water_level_status}\n\n"

            f"PRIMARY DRIVERS\n"
        )

        if result.primary_drivers:

            details += "\n".join(
                f"  - {driver}"
                for driver in result.primary_drivers
            )

        else:

            details += (
                "  - No elevated indicators."
            )

        details_label.config(
            text=details
        )

    except ValueError as e:

        messagebox.showerror(
            "Invalid Input",
            f"Please check your input.\n\n{e}",
        )

    except Exception as e:

        messagebox.showerror(
            "Error",
            f"Could not calculate the alert:\n\n{e}",
        )


# ============================================================
# BUTTONS
# ============================================================

button_frame = ttk.Frame(main)
button_frame.pack(
    fill="x",
    pady=5,
)

ttk.Button(
    button_frame,
    text="CALCULATE ALERT",
    command=calculate,
).pack(side="left")

ttk.Button(
    button_frame,
    text="EXIT",
    command=root.destroy,
).pack(side="right")


# ============================================================
# START
# ============================================================

root.mainloop()