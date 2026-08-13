import os
from pathlib import Path

import requests


USERNAME = os.environ["CDSE_USERNAME"]
PASSWORD = os.environ["CDSE_PASSWORD"]

TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/"
    "protocol/openid-connect/token"
)

PRODUCT_URL = (
    "https://zipper.dataspace.copernicus.eu/odata/v1/"
    "Products(ce2e2187-e947-4656-8b74-30d45a32f55e)/$value"
)

OUTPUT = Path(
    "data/raw/sentinel2/"
    "S2B_20251230_T45RTM_L1C.zip"
)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

print("Authenticating with Copernicus Data Space...")

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
    print("Copernicus response:")
    print(token_response.text)
    raise SystemExit("Authentication failed.")

access_token = token_response.json()["access_token"]

print("Authentication successful.")
print("Downloading:")
print("  Sentinel-2B")
print("  2025-12-30")
print("  Tile T45RTM")
print()

response = requests.get(
    PRODUCT_URL,
    headers={"Authorization": f"Bearer {access_token}"},
    stream=True,
    timeout=120,
)

response.raise_for_status()

total = int(response.headers.get("content-length", 0))
downloaded = 0

with open(OUTPUT, "wb") as f:
    for chunk in response.iter_content(chunk_size=1024 * 1024):
        if chunk:
            f.write(chunk)
            downloaded += len(chunk)

            if total:
                percent = downloaded / total * 100
                print(
                    f"\rDownloaded: {percent:6.2f}%",
                    end="",
                    flush=True,
                )

print()
print()
print("DOWNLOAD COMPLETE")
print(f"File: {OUTPUT}")
print(f"Size: {OUTPUT.stat().st_size / (1024**3):.2f} GB")