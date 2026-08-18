from pathlib import Path
import argparse
import zipfile


# =========================================================
# CONFIGURATION
# =========================================================

BASE = Path("data/raw/sentinel2")
OUTPUT_BASE = Path("data/processed/sentinel2")


# =========================================================
# FIND ZIP FILE
# =========================================================

def find_zip(date):
    date_compact = date.replace("_", "")

    matches = list(
        BASE.glob(
            f"S2?_{date_compact}_T45RTM_L1C.zip"
        )
    )

    if not matches:
        raise FileNotFoundError(
            f"No Sentinel-2 ZIP found for {date}"
        )

    if len(matches) > 1:
        raise RuntimeError(
            f"Multiple Sentinel-2 ZIP files found for {date}: "
            f"{matches}"
        )

    return matches[0]


# =========================================================
# EXTRACT ONE SCENE
# =========================================================

def extract_scene(date):

    zip_file = find_zip(date)

    output = OUTPUT_BASE / date
    output.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print(f"EXTRACTING SENTINEL-2 SCENE: {date}")
    print("=" * 60)

    print(f"Source: {zip_file}")
    print(f"Output: {output}")

    with zipfile.ZipFile(zip_file, "r") as z:
        z.extractall(output)

    print("Extraction complete.")
    print("STATUS: SUCCESS")


# =========================================================
# COMMAND-LINE INTERFACE
# =========================================================

def main():

    parser = argparse.ArgumentParser(
        description="Extract Sentinel-2 L1C ZIP products."
    )

    parser.add_argument(
        "--date",
        required=True,
        help="Scene date, e.g. 2025_12_30"
    )

    args = parser.parse_args()

    extract_scene(args.date)


if __name__ == "__main__":
    main()