"""Portable loaders for the frozen public inputs used by the GDP-tempo analyses."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DATA = Path(os.environ.get("GDP_TEMPO_SOURCE_DATA", ROOT / "source_data"))
PWT_PATH = SOURCE_DATA / "pwt1001_selected.csv"
WORLD_BANK_PATH = SOURCE_DATA / "world_bank_indicators.csv"
OECD_GFCF_PATH = SOURCE_DATA / "oecd" / "gfcf_by_asset_full.csv"


def _require(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(
            f"Required source data not found: {path}. "
            "Use the committed source_data files or set GDP_TEMPO_SOURCE_DATA."
        )
    return path


def load_pwt() -> pd.DataFrame:
    """Load the frozen PWT 10.01 extract."""
    return pd.read_csv(_require(PWT_PATH))


def load_world_bank(indicator: str) -> pd.DataFrame:
    """Load one frozen World Bank indicator as iso3/year/value rows."""
    data = pd.read_csv(_require(WORLD_BANK_PATH))
    rows = data[data["indicator"] == indicator][["iso3", "year", "value"]].copy()
    if rows.empty:
        raise ValueError(f"Indicator {indicator!r} is absent from {WORLD_BANK_PATH}")
    return rows


def load_rnd() -> pd.DataFrame:
    """Load WDI research-and-development expenditure (% of GDP)."""
    rows = load_world_bank("GB.XPD.RSDV.GD.ZS")
    return rows.rename(columns={"value": "rnd_gdp"})


def load_cwon(indicator: str) -> dict[tuple[str, int], float]:
    """Load a Changing Wealth of Nations series keyed by (ISO3, year)."""
    rows = load_world_bank(indicator)
    return {
        (row.iso3, int(row.year)): float(row.value)
        for row in rows.itertuples(index=False)
    }


def load_oecd_gfcf() -> pd.DataFrame:
    """Load the frozen OECD GFCF-by-asset extract in normalized units."""
    data = pd.read_csv(_require(OECD_GFCF_PATH))
    required = {"iso3", "asset", "year", "value"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"OECD extract is missing columns: {sorted(missing)}")
    return data[["iso3", "asset", "year", "value"]].copy()
