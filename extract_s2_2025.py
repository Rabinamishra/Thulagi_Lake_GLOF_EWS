from pathlib import Path
import zipfile

ZIP_FILE = Path("data/raw/sentinel2/S2B_20251230_T45RTM_L1C.zip")
OUTPUT = Path("data/processed/sentinel2/2025_12_30")

print("Extracting Sentinel-2 product...")
print(f"Source: {ZIP_FILE}")
print(f"Output: {OUTPUT}")

with zipfile.ZipFile(ZIP_FILE, "r") as z:
    z.extractall(OUTPUT)

print("Extraction complete.")