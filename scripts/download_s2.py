import argparse
import os
from pathlib import Path

import requests


# ============================================================
# SENTINEL-2 PRODUCTS
# ============================================================

PRODUCTS = {
    "2016_11_02": {
        "satellite": "S2A",
        "date": "2016-11-02",
        "tile": "T45RTM",
        "product_id": "62c39490-895c-4c70-9ea8-8aac69b861bd",
    },
    "2025_12_30": {
        "satellite": "S2B",
        "date": "2025-12-30",
        "tile": "T45RTM",
        "product_id": "ce2e2187-e947-4656-8b74-30d45a32f55e",
    },
}


# ============================================================
# COPERNICUS DATA SPACE
# ============================================================

TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/"
    "protocol/openid-connect/token"
)

PRODUCT_URL = (
    "https://zipper.dataspace.copernicus.eu/odata/v1/"
)


# ============================================================
# ARGUMENTS
# ============================================================

parser = argparse.ArgumentParser(
    description="Download a Sentinel-2 L1C product from Copernicus Data Space."
)

parser.add_argument(
    "--date",
    required=True,
    choices=PRODUCTS.keys(),
    help="Scene date, e.g. 2016_11_02",
)

args = parser.parse_args()

scene = PRODUCTS[args.date]


# ============================================================
# CREDENTIALS
# ============================================================

USERNAME = os.environ.get("CDSE_USERNAME")
PASSWORD = os.environ.get("CDSE_PASSWORD")

if not USERNAME or not PASSWORD:
    raise RuntimeError(
        "Copernicus credentials not found. "
        "Set CDSE_USERNAME and CDSE_PASSWORD environment variables."
    )


# ============================================================
# OUTPUT
# ============================================================

OUTPUT = Path(
    "data/raw/sentinel2"
) / (
    f"{scene['satellite']}_"
    f"{args.date.replace('_', '')}_"
    f"{scene['tile']}_L1C.zip"
)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)


# ============================================================
# PRODUCT URL
# ============================================================

product_url = (
    PRODUCT_URL
    + f"Products({scene['product_id']})/$value"
)


# ============================================================
# AUTHENTICATION
# ============================================================

print("=" * 60)
print("SENTINEL-2 DOWNLOAD")
print("=" * 60)

print("\nAuthenticating with Copernicus Data Space...")

token_response = requests.post(
    TOKEN_URL,
    data={
        "client_id": "cdse-public",
        "username": USERNAME,
        "password": PASSWORD,
        "grant_type": "password",
    },
    timeout=60,
)

if not token_response.ok:
    print("\nCopernicus response:")
    print(token_response.text)
    raise SystemExit("Authentication failed.")

access_token = token_response.json()["access_token"]

print("Authentication successful.")


# ============================================================
# DOWNLOAD
# ============================================================

print("\nDownloading:")
print(f"  Satellite: {scene['satellite']}")
print(f"  Date:      {scene['date']}")
print(f"  Tile:      {scene['tile']}")
print(f"  Output:    {OUTPUT}")
print()

response = requests.get(
    product_url,
    headers={
        "Authorization": f"Bearer {access_token}"
    },
    stream=True,
    timeout=120,
)

response.raise_for_status()

total = int(
    response.headers.get("content-length", 0)
)

downloaded = 0

with open(OUTPUT, "wb") as f:

    for chunk in response.iter_content(
        chunk_size=1024 * 1024
    ):

        if not chunk:
            continue

        f.write(chunk)
        downloaded += len(chunk)

        if total:
            percent = (
                downloaded / total * 100
            )

            print(
                f"\rDownloaded: {percent:6.2f}%",
                end="",
                flush=True,
            )

print()
print()
print("=" * 60)
print("DOWNLOAD COMPLETE")
print("=" * 60)

print(f"File: {OUTPUT}")

print(
    f"Size: "
    f"{OUTPUT.stat().st_size / (1024 ** 3):.2f} GB"
)