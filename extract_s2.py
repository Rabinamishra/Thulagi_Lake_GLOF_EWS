from pathlib import Path
import zipfile

ZIP_FILE = Path("data/raw/sentinel2/S2A_20161102_T45RTM_L1C.zip")
OUTPUT = Path("data/processed/sentinel2/2016_11_02")

OUTPUT.mkdir(parents=True, exist_ok=True)

print("Extracting Sentinel-2 product...")
print(f"Source: {ZIP_FILE}")
print(f"Output: {OUTPUT}")

with zipfile.ZipFile(ZIP_FILE, "r") as z:
    z.extractall(OUTPUT)

print("Extraction complete.")