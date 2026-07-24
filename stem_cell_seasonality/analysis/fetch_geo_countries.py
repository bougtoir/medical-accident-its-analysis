#!/usr/bin/env python3
"""
Fetch contact_country from GEO SOFT headers for all cached accessions.
Uses batched requests with rate limiting.
Outputs: geo_country_full.csv
"""

import os
import time
import requests
import pandas as pd

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

SOUTHERN_HEMISPHERE = {
    "australia", "new zealand", "brazil", "argentina", "south africa",
    "chile", "peru", "colombia", "indonesia", "madagascar", "mozambique",
    "zimbabwe", "zambia", "uruguay", "paraguay", "bolivia", "ecuador",
    "kenya", "tanzania", "papua new guinea", "fiji",
}

COUNTRY_LAT = {
    "usa": 38, "united states": 38, "china": 35, "united kingdom": 52,
    "germany": 51, "japan": 36, "netherlands": 52, "australia": -34,
    "italy": 42, "belgium": 51, "spain": 40, "canada": 45, "france": 46,
    "south korea": 37, "singapore": 1, "taiwan": 25, "israel": 32,
    "sweden": 59, "austria": 47, "denmark": 56, "switzerland": 47,
    "brazil": -23, "india": 20, "finland": 61, "norway": 60,
    "ireland": 53, "portugal": 39, "czech republic": 50, "poland": 52,
    "argentina": -34, "new zealand": -41, "south africa": -34,
    "chile": -33, "hungary": 47, "greece": 38, "hong kong": 22,
    "russia": 56, "turkey": 39, "mexico": 19, "thailand": 14,
    "malaysia": 3, "saudi arabia": 24, "iran": 32, "egypt": 30,
    "colombia": 5, "peru": -12,
}


def fetch_country(accession, timeout=15):
    """Fetch contact_country from GEO SOFT brief format."""
    url = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"
    params = {"acc": accession, "targ": "self", "form": "text", "view": "brief"}
    try:
        resp = requests.get(url, params=params, timeout=timeout)
        for line in resp.text.split("\n"):
            if "!Series_contact_country" in line:
                return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return None


def main():
    geo_csv = os.path.join(OUTPUT_DIR, "geo_psc_metadata.csv")
    country_csv = os.path.join(OUTPUT_DIR, "geo_country_full.csv")

    df = pd.read_csv(geo_csv)
    accessions = df["accession"].tolist()
    print(f"Total accessions: {len(accessions)}")

    # Load existing results if resuming
    existing = {}
    if os.path.exists(country_csv):
        prev = pd.read_csv(country_csv)
        existing = dict(zip(prev["accession"], prev["country"]))
        print(f"Loaded {len(existing)} existing country records")

    remaining = [a for a in accessions if a not in existing]
    print(f"Remaining to fetch: {len(remaining)}")

    results = dict(existing)
    for i, acc in enumerate(remaining):
        country = fetch_country(acc)
        if country:
            results[acc] = country

        if (i + 1) % 100 == 0:
            print(f"  Processed {i+1}/{len(remaining)}, total found: {len(results)}")
            # Save checkpoint
            pd.DataFrame(list(results.items()), columns=["accession", "country"]).to_csv(
                country_csv, index=False
            )

        time.sleep(0.35)

    # Final save
    out_df = pd.DataFrame(list(results.items()), columns=["accession", "country"])
    out_df.to_csv(country_csv, index=False)
    print(f"\nSaved {len(out_df)} records to {country_csv}")

    # Summary
    from collections import Counter
    c = Counter(results.values())
    print("\nTop 20 countries:")
    for country, cnt in c.most_common(20):
        print(f"  {country}: {cnt}")

    # Hemisphere
    nh = sh = eq = 0
    for country in results.values():
        cl = country.lower().strip()
        if cl in SOUTHERN_HEMISPHERE:
            sh += 1
        else:
            nh += 1
    print(f"\nNorthern Hemisphere: {nh}")
    print(f"Southern Hemisphere: {sh}")


if __name__ == "__main__":
    main()
