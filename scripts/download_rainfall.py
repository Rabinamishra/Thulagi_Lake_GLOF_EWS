import requests
import pandas as pd
from pathlib import Path

# --------------------------------------------------
# THULAGI LAKE RAINFALL DOWNLOAD
# NASA POWER Daily API
# --------------------------------------------------

LATITUDE = 28.493999
LONGITUDE = 84.482029

START_DATE = "20010101"
END_DATE = "20260812"

OUTPUT = Path("data/rainfall/rainfall_daily.csv")

url = (
    "https://power.larc.nasa.gov/api/temporal/daily/point"
    f"?parameters=PRECTOTCORR"
    f"&community=AG"
    f"&longitude={LONGITUDE}"
    f"&latitude={LATITUDE}"
    f"&start={START_DATE}"
    f"&end={END_DATE}"
    f"&format=JSON"
)

print("Downloading Thulagi rainfall data...")
print(f"Location: {LATITUDE}, {LONGITUDE}")
print(f"Period: {START_DATE} to {END_DATE}")

response = requests.get(url, timeout=60)
response.raise_for_status()

data = response.json()

rainfall = data["properties"]["parameter"]["PRECTOTCORR"]

df = pd.DataFrame(
    list(rainfall.items()),
    columns=["date", "rainfall_mm"]
)

df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
df["rainfall_mm"] = pd.to_numeric(df["rainfall_mm"], errors="coerce")

# Remove missing/invalid values
df.loc[df["rainfall_mm"] < 0, "rainfall_mm"] = pd.NA

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT, index=False)

print()
print("SUCCESS")
print(f"Records: {len(df):,}")
print(f"Output: {OUTPUT}")
print()
print(df.head())
print()
print(df.tail())