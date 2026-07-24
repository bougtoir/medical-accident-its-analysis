"""
Fetch the World Bank indicators required by the tempo model-selection
analysis and cache them under data/wb/ in the repository.

Indicators:
  SH.XPD.CHEX.PP.CD  Current health expenditure per capita, PPP (current int$)
  SH.XPD.CHEX.GD.ZS  Current health expenditure (% of GDP)
  SP.DYN.LE00.IN     Life expectancy at birth, total (years)

Each file is written as data/wb/<indicator>.json in the World Bank API
"data" array format: a list of records with keys countryiso3code, date,
value. This is the exact format consumed by tempo_model_selection.load_wb().

Usage:
    python scripts/fetch_wb_health.py

Requires network access to https://api.worldbank.org. The committed
data/wb/ subset already contains these files for the countries used in the
analysis, so a clean clone can reproduce the results offline; run this
script only to refresh from the live API.
"""
import os
import json
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
WB_DIR = os.path.join(ROOT, "data", "wb")
os.makedirs(WB_DIR, exist_ok=True)

INDICATORS = [
    "SH.XPD.CHEX.PP.CD",
    "SH.XPD.CHEX.GD.ZS",
    "SP.DYN.LE00.IN",
]

BASE = ("https://api.worldbank.org/v2/country/all/indicator/{code}"
        "?format=json&per_page=20000&date=2000:2023")


def fetch_indicator(code):
    url = BASE.format(code=code)
    with urllib.request.urlopen(url, timeout=120) as resp:
        payload = json.load(resp)
    if not isinstance(payload, list) or len(payload) < 2:
        raise RuntimeError(f"Unexpected World Bank response for {code}")
    return payload[1]


def main():
    for code in INDICATORS:
        print(f"Fetching {code} ...", flush=True)
        for attempt in range(3):
            try:
                rows = fetch_indicator(code)
                break
            except Exception as exc:  # noqa: BLE001
                print(f"  attempt {attempt + 1} failed: {exc}", flush=True)
                time.sleep(5)
        else:
            raise SystemExit(f"Failed to fetch {code} after 3 attempts")
        out = os.path.join(WB_DIR, f"{code}.json")
        with open(out, "w") as fh:
            json.dump(rows, fh)
        print(f"  saved {len(rows)} records -> {out}", flush=True)


if __name__ == "__main__":
    main()
