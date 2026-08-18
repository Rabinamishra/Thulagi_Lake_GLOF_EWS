import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# --------------------------------------------------
# LOCKED THULAGI LAKE AREA DATA
# --------------------------------------------------

data = pd.DataFrame({
    "year": [2016, 2018, 2020, 2022, 2024, 2025],
    "area_km2": [0.8270, 0.8627, 0.8844, 0.9209, 0.9167, 0.9291]
})

# --------------------------------------------------
# CALCULATE CHANGES
# --------------------------------------------------

data["change_km2"] = data["area_km2"].diff()

data["change_percent"] = (
    data["area_km2"].pct_change() * 100
)

data["annual_change_km2_per_year"] = (
    data["change_km2"] / data["year"].diff()
)

# --------------------------------------------------
# OVERALL CHANGE
# --------------------------------------------------

overall_change = data.iloc[-1]["area_km2"] - data.iloc[0]["area_km2"]

overall_percent = (
    overall_change / data.iloc[0]["area_km2"] * 100
)

overall_annual_change = (
    overall_change /
    (data.iloc[-1]["year"] - data.iloc[0]["year"])
)

# --------------------------------------------------
# OUTPUT DIRECTORIES
# --------------------------------------------------

results = Path("results")
tables = results / "tables"
figures = results / "figures"

tables.mkdir(parents=True, exist_ok=True)
figures.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# SAVE TABLE
# --------------------------------------------------

output_csv = tables / "lake_area_timeseries.csv"

data.to_csv(output_csv, index=False)

# --------------------------------------------------
# PRINT RESULTS
# --------------------------------------------------

print("\nTHULAGI LAKE AREA ANALYSIS")
print("=" * 40)

print(data.to_string(index=False))

print("\nOVERALL 2016–2025")
print("=" * 40)

print(f"Initial area:       {data.iloc[0]['area_km2']:.4f} km²")
print(f"Final area:         {data.iloc[-1]['area_km2']:.4f} km²")
print(f"Total change:       {overall_change:+.4f} km²")
print(f"Percentage change:  {overall_percent:+.2f}%")
print(f"Average annual:     {overall_annual_change:+.5f} km²/year")

print(f"\nSaved: {output_csv}")

# --------------------------------------------------
# PLOT
# --------------------------------------------------

plt.figure(figsize=(9, 5))

plt.plot(
    data["year"],
    data["area_km2"],
    marker="o",
    linewidth=2
)

plt.xlabel("Year")
plt.ylabel("Lake area (km²)")
plt.title("Thulagi Lake Area, 2016–2025")

plt.grid(True, alpha=0.3)
plt.tight_layout()

output_figure = figures / "thulagi_lake_area_trend_2016_2025.png"

plt.savefig(
    output_figure,
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print(f"Saved: {output_figure}")