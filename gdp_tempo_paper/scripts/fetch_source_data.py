"""Refresh or independently verify the frozen public source-data extracts.

The reproduction pipeline uses committed, checksummed extracts so it does not
change when providers revise their APIs. This utility downloads fresh PWT/WB
copies for provenance checks. OECD's live dataflow can also be downloaded for
manual vintage comparison, but it is not substituted automatically because the
provider revises observations and ordering over time.
"""
from __future__ import annotations

import argparse
import io
import tarfile
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from data_sources import SOURCE_DATA

ISO3 = (
    "AUS", "AUT", "BEL", "CAN", "CHL", "CHN", "COL", "CRI", "CZE",
    "DNK", "EST", "FIN", "FRA", "DEU", "GRC", "HUN", "ISL", "IRL",
    "ISR", "ITA", "JPN", "KOR", "LVA", "LTU", "LUX", "MEX", "NLD",
    "NZL", "NOR", "POL", "PRT", "SVK", "SVN", "ESP", "SWE", "CHE",
    "TUR", "GBR", "USA",
)
PWT_URL = "https://cloud.r-project.org/src/contrib/pwt10_10.01-0.tar.gz"
WB_INDICATORS = (
    "GB.XPD.RSDV.GD.ZS",
    "NW.PCA.TO",
    "NW.HCA.TO",
    "NW.TOW.TO",
)
WB_URL = "https://api.worldbank.org/v2/country/all/indicator/{indicator}?format=json&per_page=30000"
OECD_URL = (
    "https://sdmx.oecd.org/public/rest/v1/data/"
    "OECD.SDD.NAD,DSD_NAMAIN10@DF_TABLE1_EXPENDITURE_GFCF_ASSET,/."
    "?startPeriod=1970"
)


def download(url: str, *, timeout: int) -> bytes:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.content


def fetch_pwt(timeout: int) -> pd.DataFrame:
    try:
        import pyreadr
    except ImportError as exc:
        raise RuntimeError("Install requirements-refresh.txt to refresh PWT") from exc

    archive = download(PWT_URL, timeout=timeout)
    with tempfile.TemporaryDirectory() as directory:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
            member = tar.getmember("pwt10/data/pwt10.01.rda")
            tar.extract(member, directory, filter="data")
        path = Path(directory) / member.name
        data = pyreadr.read_r(str(path))["pwt10.01"].reset_index(drop=True)

    columns = [
        "country", "isocode", "year", "rgdpna", "rnna", "emp", "avh",
        "hc", "labsh", "csh_i", "delta",
    ]
    data = data[columns].rename(columns={"isocode": "iso3"})
    data["country"] = data["country"].astype(str)
    data["iso3"] = data["iso3"].astype(str)
    data = data[data["iso3"].isin(ISO3)].copy()
    data.loc[data["iso3"].eq("USA"), "country"] = "United States"
    return data.sort_values(["iso3", "year"]).reset_index(drop=True)


def fetch_world_bank(timeout: int) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for indicator in WB_INDICATORS:
        payload = requests.get(WB_URL.format(indicator=indicator), timeout=timeout)
        payload.raise_for_status()
        body = payload.json()
        observations = body[1] if isinstance(body, list) and len(body) == 2 else body
        for observation in observations:
            iso3 = observation.get("countryiso3code")
            value = observation.get("value")
            if iso3 in ISO3 and value is not None:
                rows.append({
                    "indicator": indicator,
                    "iso3": iso3,
                    "year": int(observation["date"]),
                    "value": float(value),
                })
    return pd.DataFrame(rows).sort_values(
        ["indicator", "iso3", "year"]
    ).reset_index(drop=True)


def compare_numeric(downloaded: pd.DataFrame, frozen: pd.DataFrame, keys: list[str]) -> tuple[int, float]:
    merged = frozen.merge(downloaded, on=keys, how="outer", suffixes=("_frozen", "_downloaded"), indicator=True)
    missing = int((merged["_merge"] != "both").sum())
    both = merged[merged["_merge"] == "both"]
    numeric = [
        column.removesuffix("_frozen")
        for column in both.columns
        if column.endswith("_frozen") and pd.api.types.is_numeric_dtype(both[column])
    ]
    differences = []
    for column in numeric:
        left = both[f"{column}_frozen"].to_numpy(dtype=float)
        right = both[f"{column}_downloaded"].to_numpy(dtype=float)
        finite = np.isfinite(left) & np.isfinite(right)
        if finite.any():
            differences.append(float(np.max(np.abs(left[finite] - right[finite]))))
    return missing, max(differences, default=0.0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="replace the frozen PWT/WB extracts")
    parser.add_argument("--download-oecd-current", type=Path, help="save the live OECD CSV for manual vintage comparison")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    pwt = fetch_pwt(args.timeout)
    world_bank = fetch_world_bank(args.timeout)

    if args.refresh:
        pwt.to_csv(SOURCE_DATA / "pwt1001_selected.csv", index=False)
        world_bank.to_csv(SOURCE_DATA / "world_bank_indicators.csv", index=False)
        print("Refreshed PWT and World Bank extracts; update checksums and rerun validation.")
    else:
        frozen_pwt = pd.read_csv(SOURCE_DATA / "pwt1001_selected.csv").sort_values(["iso3", "year"]).reset_index(drop=True)
        frozen_wb = pd.read_csv(SOURCE_DATA / "world_bank_indicators.csv").sort_values(["indicator", "iso3", "year"]).reset_index(drop=True)
        pwt_missing, pwt_difference = compare_numeric(pwt, frozen_pwt, ["country", "iso3", "year"])
        wb_missing, wb_difference = compare_numeric(world_bank, frozen_wb, ["indicator", "iso3", "year"])
        print(f"PWT: unmatched rows={pwt_missing}, max numeric difference={pwt_difference:.3g}")
        print(f"World Bank: unmatched rows={wb_missing}, max numeric difference={wb_difference:.3g}")
        if pwt_missing or wb_missing or pwt_difference > 1e-9 or wb_difference > 1e-9:
            raise SystemExit("Live provider data differ from the frozen research vintage.")

    if args.download_oecd_current:
        args.download_oecd_current.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(OECD_URL, headers={"Accept": "text/csv"}, timeout=args.timeout)
        response.raise_for_status()
        args.download_oecd_current.write_bytes(response.content)
        print(f"Saved current OECD dataflow to {args.download_oecd_current}")


if __name__ == "__main__":
    main()
