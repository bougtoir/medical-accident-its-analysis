#!/usr/bin/env python3
"""
Exploratory analysis: GEO iPSC/ESC differentiation metadata × seasonal/solar patterns.

Analysis 1: GEO metadata × season/latitude (Northern vs Southern hemisphere)
Analysis 2: GEO metadata × solar activity/geomagnetic indices (NOAA)

Data sources:
- NCBI GEO (Entrez E-utilities): iPSC/ESC differentiation dataset metadata
- NOAA SWPC: Monthly solar cycle indices (SSN, F10.7, Ap)
"""

import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from xml.etree import ElementTree as ET

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import requests
from scipy import stats

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

ENTREZ_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
NOAA_SOLAR_URL = "https://services.swpc.noaa.gov/json/solar-cycle/observed-solar-cycle-indices.json"

# Geocoding cache for known GEO contributor countries/institutions → approximate latitude
INSTITUTION_LAT = {
    # Northern hemisphere major iPSC hubs
    "japan": 36, "tokyo": 36, "kyoto": 35, "osaka": 35, "riken": 35,
    "usa": 38, "united states": 38, "boston": 42, "san diego": 33,
    "stanford": 37, "harvard": 42, "nih": 39, "mit": 42,
    "uk": 52, "united kingdom": 52, "cambridge": 52, "oxford": 52, "london": 52,
    "germany": 51, "berlin": 52, "heidelberg": 49, "munich": 48,
    "france": 46, "paris": 49,
    "china": 35, "beijing": 40, "shanghai": 31, "guangzhou": 23,
    "korea": 37, "seoul": 37,
    "canada": 45, "toronto": 44, "vancouver": 49,
    "sweden": 59, "karolinska": 59,
    "switzerland": 47, "zurich": 47,
    "netherlands": 52, "amsterdam": 52,
    "israel": 32, "weizmann": 32,
    "italy": 42, "rome": 42,
    "spain": 40, "barcelona": 41,
    "singapore": 1,
    "india": 20, "bangalore": 13,
    "taiwan": 25, "taipei": 25,
    # Southern hemisphere
    "australia": -34, "melbourne": -38, "sydney": -34, "perth": -32, "brisbane": -27,
    "new zealand": -41, "auckland": -37,
    "brazil": -23, "sao paulo": -24, "rio": -23,
    "argentina": -34, "buenos aires": -35,
    "south africa": -34, "cape town": -34,
    "chile": -33, "santiago": -33,
}


def entrez_search(query, db="gds", retmax=5000):
    """Search GEO via Entrez and return UIDs."""
    url = f"{ENTREZ_BASE}/esearch.fcgi"
    params = {
        "db": db,
        "term": query,
        "retmax": retmax,
        "retmode": "json",
        "usehistory": "y",
    }
    resp = requests.get(url, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    result = data.get("esearchresult", {})
    count = int(result.get("count", 0))
    ids = result.get("idlist", [])
    webenv = result.get("webenv", "")
    query_key = result.get("querykey", "")
    print(f"  Search returned {count} results, fetched {len(ids)} UIDs")
    return ids, webenv, query_key, count


def entrez_summary_batch(ids, db="gds", batch_size=200):
    """Fetch summaries for a list of UIDs in batches."""
    all_summaries = []
    for i in range(0, len(ids), batch_size):
        batch = ids[i:i+batch_size]
        url = f"{ENTREZ_BASE}/esummary.fcgi"
        params = {
            "db": db,
            "id": ",".join(batch),
            "retmode": "json",
        }
        resp = requests.get(url, params=params, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        result = data.get("result", {})
        for uid in batch:
            if uid in result:
                all_summaries.append(result[uid])
        print(f"  Fetched summaries {i+1}–{min(i+batch_size, len(ids))} of {len(ids)}")
        time.sleep(0.4)  # respect NCBI rate limits
    return all_summaries


def infer_latitude(summary):
    """Infer approximate latitude from GEO summary metadata."""
    # Use 'contact' field which often has institution/country info
    text_fields = " ".join([
        str(summary.get("title", "")),
        str(summary.get("summary", "")),
        str(summary.get("gpl", "")),
    ]).lower()

    # Word-boundary matching to avoid substring false positives
    # (e.g., "mit" matching "submitted", "rio" matching "prior")
    for keyword, lat in sorted(INSTITUTION_LAT.items(), key=lambda x: len(x[0]), reverse=True):
        # Use word boundary regex for short keywords (<=4 chars)
        if len(keyword) <= 4:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_fields):
                return lat, keyword
        else:
            if keyword in text_fields:
                return lat, keyword
    return None, None


def parse_geo_date(summary):
    """Extract submission date from GEO summary."""
    pdat = summary.get("pdat", "")
    if pdat:
        try:
            return datetime.strptime(pdat, "%Y/%m/%d")
        except ValueError:
            pass
    return None


def fetch_noaa_solar_indices():
    """Fetch NOAA monthly solar cycle indices (SSN, F10.7, Ap)."""
    print("Fetching NOAA solar indices...")
    resp = requests.get(NOAA_SOLAR_URL, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    records = []
    for entry in data:
        tt = entry.get("time-tag", "")
        try:
            dt = datetime.strptime(tt, "%Y-%m")
        except ValueError:
            continue
        records.append({
            "date": dt,
            "year": dt.year,
            "month": dt.month,
            "ssn": entry.get("ssn"),
            "smoothed_ssn": entry.get("smoothed_ssn"),
            "f10.7": entry.get("f10.7"),
            "smoothed_f10.7": entry.get("smoothed_f10.7"),
        })

    df = pd.DataFrame(records)
    # Convert numeric columns
    for col in ["ssn", "smoothed_ssn", "f10.7", "smoothed_f10.7"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    print(f"  NOAA data: {len(df)} months, {df['date'].min()} to {df['date'].max()}")
    return df


def fetch_geo_metadata():
    """Search GEO for iPSC/ESC differentiation datasets and extract metadata."""
    queries = [
        '("iPSC" OR "induced pluripotent") AND "differentiation" AND gse[Entry Type]',
        '("embryonic stem cell" OR "ESC" OR "hESC") AND "differentiation" AND gse[Entry Type]',
        '"pluripotent stem cell" AND "directed differentiation" AND gse[Entry Type]',
    ]

    all_ids = set()
    for q in queries:
        print(f"\nSearching GEO: {q[:80]}...")
        ids, _, _, count = entrez_search(q)
        all_ids.update(ids)
        time.sleep(0.5)

    print(f"\nTotal unique GEO Series IDs: {len(all_ids)}")

    # Fetch summaries
    print("Fetching summaries...")
    summaries = entrez_summary_batch(list(all_ids))
    print(f"Fetched {len(summaries)} summaries")

    # Parse into structured records
    records = []
    for s in summaries:
        dt = parse_geo_date(s)
        if dt is None:
            continue

        lat, loc_keyword = infer_latitude(s)
        hemisphere = None
        if lat is not None:
            hemisphere = "Northern" if lat > 0 else "Southern"

        n_samples = s.get("n_samples", 0)
        try:
            n_samples = int(n_samples)
        except (ValueError, TypeError):
            n_samples = 0

        records.append({
            "uid": s.get("uid", ""),
            "accession": s.get("accession", ""),
            "title": s.get("title", ""),
            "date": dt,
            "year": dt.year,
            "month": dt.month,
            "quarter": (dt.month - 1) // 3 + 1,
            "season_nh": ["Winter", "Winter", "Spring", "Spring", "Spring",
                          "Summer", "Summer", "Summer", "Fall", "Fall",
                          "Fall", "Winter"][dt.month - 1],
            "latitude": lat,
            "loc_keyword": loc_keyword,
            "hemisphere": hemisphere,
            "n_samples": n_samples,
            "taxon": s.get("taxon", ""),
            "gpl": s.get("gpl", ""),
            "ptype": s.get("ptype", ""),
        })

    df = pd.DataFrame(records)
    print(f"\nParsed {len(df)} records with valid dates")
    if len(df) > 0:
        print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"  Hemisphere assignment: {df['hemisphere'].value_counts().to_dict()}")
        print(f"  Missing hemisphere: {df['hemisphere'].isna().sum()}")
    return df


# ──────────────────────────────────────────────
# Analysis 1: Seasonal distribution by hemisphere
# ──────────────────────────────────────────────
def analysis_seasonal(geo_df):
    """Analyze seasonal distribution of GEO submissions by hemisphere."""
    print("\n" + "="*60)
    print("ANALYSIS 1: Seasonal Distribution by Hemisphere")
    print("="*60)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 1a: Monthly distribution (all data)
    ax = axes[0, 0]
    month_counts = geo_df.groupby("month").size()
    ax.bar(range(1, 13), [month_counts.get(m, 0) for m in range(1, 13)],
           color='steelblue', alpha=0.8)
    ax.set_xlabel("Month")
    ax.set_ylabel("Number of GEO Series")
    ax.set_title("(A) Monthly distribution of PSC differentiation datasets (all)")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], rotation=45)

    # 1b: Monthly distribution by hemisphere
    ax = axes[0, 1]
    nh = geo_df[geo_df["hemisphere"] == "Northern"]
    sh = geo_df[geo_df["hemisphere"] == "Southern"]
    nh_counts = nh.groupby("month").size()
    sh_counts = sh.groupby("month").size()

    x = np.arange(1, 13)
    width = 0.35
    ax.bar(x - width/2, [nh_counts.get(m, 0) for m in range(1, 13)],
           width, label=f"Northern (n={len(nh)})", color='royalblue', alpha=0.8)
    ax.bar(x + width/2, [sh_counts.get(m, 0) for m in range(1, 13)],
           width, label=f"Southern (n={len(sh)})", color='coral', alpha=0.8)
    ax.set_xlabel("Month")
    ax.set_ylabel("Number of GEO Series")
    ax.set_title("(B) Monthly distribution by hemisphere")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], rotation=45)
    ax.legend()

    # 1c: Normalized seasonal pattern — if hemisphere inverted, expect mirror
    ax = axes[1, 0]
    # Map NH months to "months from summer solstice" for both hemispheres
    # NH summer solstice = month 6 (June), SH summer solstice = month 12 (Dec)
    def months_from_local_summer(month, hemisphere):
        if hemisphere == "Northern":
            return (month - 6) % 12  # 0=June, 6=December
        else:
            return (month - 12) % 12  # 0=December, 6=June

    if len(nh) > 0 and len(sh) > 0:
        nh_local = nh["month"].apply(lambda m: months_from_local_summer(m, "Northern"))
        sh_local = sh["month"].apply(lambda m: months_from_local_summer(m, "Southern"))

        nh_local_counts = nh_local.value_counts().sort_index()
        sh_local_counts = sh_local.value_counts().sort_index()

        # Normalize
        nh_norm = nh_local_counts / nh_local_counts.sum()
        sh_norm = sh_local_counts / sh_local_counts.sum()

        local_months = range(0, 12)
        local_labels = [f"+{m}" for m in local_months]

        ax.plot([nh_norm.get(m, 0) for m in local_months], 'b-o',
                label=f"Northern (n={len(nh)})", markersize=6)
        ax.plot([sh_norm.get(m, 0) for m in local_months], 'r-s',
                label=f"Southern (n={len(sh)})", markersize=6)
        ax.set_xlabel("Months from local summer solstice")
        ax.set_ylabel("Proportion of submissions")
        ax.set_title("(C) Aligned by local summer solstice")
        ax.set_xticks(range(12))
        ax.set_xticklabels(local_labels, fontsize=8)
        ax.legend()
    else:
        ax.text(0.5, 0.5, "Insufficient Southern\nHemisphere data",
                ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.set_title("(C) Aligned by local summer solstice")

    # 1d: Yearly trend
    ax = axes[1, 1]
    year_counts = geo_df.groupby("year").size()
    ax.bar(year_counts.index, year_counts.values, color='teal', alpha=0.7)
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of GEO Series")
    ax.set_title("(D) Annual trend of PSC differentiation datasets")

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "analysis1_seasonal_distribution.png")
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out_path}")

    # Statistical tests
    print("\n  Statistical tests:")
    if len(geo_df) > 0:
        month_counts_arr = [geo_df[geo_df["month"] == m].shape[0] for m in range(1, 13)]
        chi2, p = stats.chisquare(month_counts_arr)
        print(f"    Chi-square test (uniform monthly distribution): χ²={chi2:.2f}, p={p:.4f}")

    if len(nh) > 10 and len(sh) > 10:
        # Rayleigh test equivalent: circular mean test
        # Convert months to radians
        nh_angles = nh["month"].values * 2 * np.pi / 12
        sh_angles = sh["month"].values * 2 * np.pi / 12

        nh_mean_cos = np.mean(np.cos(nh_angles))
        nh_mean_sin = np.mean(np.sin(nh_angles))
        nh_R = np.sqrt(nh_mean_cos**2 + nh_mean_sin**2)
        nh_mean_angle = np.arctan2(nh_mean_sin, nh_mean_cos)
        nh_mean_month = (nh_mean_angle * 12 / (2 * np.pi)) % 12

        sh_mean_cos = np.mean(np.cos(sh_angles))
        sh_mean_sin = np.mean(np.sin(sh_angles))
        sh_R = np.sqrt(sh_mean_cos**2 + sh_mean_sin**2)
        sh_mean_angle = np.arctan2(sh_mean_sin, sh_mean_cos)
        sh_mean_month = (sh_mean_angle * 12 / (2 * np.pi)) % 12

        print(f"    NH circular mean month: {nh_mean_month:.1f}, R={nh_R:.3f}")
        print(f"    SH circular mean month: {sh_mean_month:.1f}, R={sh_R:.3f}")

        # Rayleigh test: z = n * R^2
        nh_z = len(nh) * nh_R**2
        sh_z = len(sh) * sh_R**2
        nh_p_rayleigh = np.exp(-nh_z)  # approximate for large n
        sh_p_rayleigh = np.exp(-sh_z)
        print(f"    NH Rayleigh test: z={nh_z:.2f}, p≈{nh_p_rayleigh:.4f}")
        print(f"    SH Rayleigh test: z={sh_z:.2f}, p≈{sh_p_rayleigh:.4f}")

    return fig


# ──────────────────────────────────────────────
# Analysis 2: GEO × Solar/Geomagnetic activity
# ──────────────────────────────────────────────
def analysis_solar(geo_df, solar_df):
    """Correlate GEO submission patterns with solar/geomagnetic activity."""
    print("\n" + "="*60)
    print("ANALYSIS 2: GEO Metadata × Solar/Geomagnetic Activity")
    print("="*60)

    # Aggregate GEO data by year-month
    geo_monthly = geo_df.groupby(["year", "month"]).agg(
        n_datasets=("uid", "count"),
        mean_samples=("n_samples", "mean"),
    ).reset_index()
    geo_monthly["date"] = pd.to_datetime(
        geo_monthly["year"].astype(str) + "-" + geo_monthly["month"].astype(str).str.zfill(2),
        format="%Y-%m"
    )

    # Merge with solar data
    solar_df["year_month"] = solar_df["date"].dt.to_period("M")
    geo_monthly["year_month"] = geo_monthly["date"].dt.to_period("M")
    merged = geo_monthly.merge(solar_df, on="year_month", how="inner", suffixes=("", "_solar"))

    print(f"  Merged records: {len(merged)} months")

    if len(merged) < 12:
        print("  Insufficient data for solar correlation analysis")
        return None

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 2a: Dataset count vs Sunspot Number over time
    ax = axes[0, 0]
    ax2 = ax.twinx()
    ax.bar(merged["date"], merged["n_datasets"], width=25, alpha=0.5,
           color='steelblue', label="GEO datasets/month")
    ax2.plot(merged["date_solar"], merged["smoothed_ssn"], 'r-', linewidth=2,
             label="Smoothed SSN")
    ax.set_xlabel("Date")
    ax.set_ylabel("GEO datasets/month", color='steelblue')
    ax2.set_ylabel("Smoothed Sunspot Number", color='red')
    ax.set_title("(A) PSC differentiation datasets vs. Solar cycle")
    ax.xaxis.set_major_locator(mdates.YearLocator(5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=8)

    # 2b: Scatter: monthly dataset count vs F10.7
    ax = axes[0, 1]
    valid = merged.dropna(subset=["n_datasets", "f10.7"])
    if len(valid) > 10:
        ax.scatter(valid["f10.7"], valid["n_datasets"], alpha=0.4,
                  s=20, color='steelblue')
        # Linear regression
        slope, intercept, r, p, se = stats.linregress(valid["f10.7"], valid["n_datasets"])
        x_fit = np.linspace(valid["f10.7"].min(), valid["f10.7"].max(), 100)
        ax.plot(x_fit, slope * x_fit + intercept, 'r-', linewidth=2,
                label=f"r={r:.3f}, p={p:.4f}")
        ax.legend(fontsize=10)
        print(f"  F10.7 vs dataset count: r={r:.3f}, p={p:.4f}")
    ax.set_xlabel("F10.7 Solar Radio Flux (sfu)")
    ax.set_ylabel("GEO datasets/month")
    ax.set_title("(B) Dataset count vs. F10.7 radio flux")

    # 2c: Scatter: dataset count vs Ap (geomagnetic)
    # Ap is not in the monthly solar cycle JSON, so we'll use SSN as proxy
    # Actually, let's check if "ap" is available... the observed-solar-cycle-indices
    # doesn't include Ap directly. We'll do SSN correlation instead and note this.
    ax = axes[1, 0]
    valid = merged.dropna(subset=["n_datasets", "ssn"])
    if len(valid) > 10:
        ax.scatter(valid["ssn"], valid["n_datasets"], alpha=0.4,
                  s=20, color='darkorange')
        slope, intercept, r, p, se = stats.linregress(valid["ssn"], valid["n_datasets"])
        x_fit = np.linspace(valid["ssn"].min(), valid["ssn"].max(), 100)
        ax.plot(x_fit, slope * x_fit + intercept, 'r-', linewidth=2,
                label=f"r={r:.3f}, p={p:.4f}")
        ax.legend(fontsize=10)
        print(f"  SSN vs dataset count: r={r:.3f}, p={p:.4f}")
    ax.set_xlabel("Monthly Sunspot Number")
    ax.set_ylabel("GEO datasets/month")
    ax.set_title("(C) Dataset count vs. Sunspot Number")

    # 2d: Detrended analysis — remove yearly trend, look at residual × solar
    ax = axes[1, 1]
    if len(merged) > 24:
        # Simple detrending: subtract 12-month rolling mean
        merged_sorted = merged.sort_values("date").copy()
        merged_sorted["n_datasets_trend"] = merged_sorted["n_datasets"].rolling(
            12, center=True, min_periods=6
        ).mean()
        merged_sorted["n_datasets_detrended"] = (
            merged_sorted["n_datasets"] - merged_sorted["n_datasets_trend"]
        )
        merged_sorted["ssn_trend"] = merged_sorted["ssn"].rolling(
            12, center=True, min_periods=6
        ).mean()
        merged_sorted["ssn_detrended"] = (
            merged_sorted["ssn"] - merged_sorted["ssn_trend"]
        )

        valid_dt = merged_sorted.dropna(
            subset=["n_datasets_detrended", "ssn_detrended"]
        )
        if len(valid_dt) > 10:
            ax.scatter(valid_dt["ssn_detrended"], valid_dt["n_datasets_detrended"],
                      alpha=0.4, s=20, color='green')
            slope, intercept, r, p, se = stats.linregress(
                valid_dt["ssn_detrended"], valid_dt["n_datasets_detrended"]
            )
            x_fit = np.linspace(valid_dt["ssn_detrended"].min(),
                               valid_dt["ssn_detrended"].max(), 100)
            ax.plot(x_fit, slope * x_fit + intercept, 'r-', linewidth=2,
                    label=f"r={r:.3f}, p={p:.4f}")
            ax.legend(fontsize=10)
            print(f"  Detrended SSN vs dataset count: r={r:.3f}, p={p:.4f}")
    ax.set_xlabel("SSN (detrended)")
    ax.set_ylabel("Dataset count (detrended)")
    ax.set_title("(D) Detrended: residual correlation")

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "analysis2_solar_correlation.png")
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out_path}")

    return fig


def save_summary_report(geo_df, solar_df):
    """Save a text summary of the analysis results."""
    out_path = os.path.join(OUTPUT_DIR, "analysis_summary.md")
    with open(out_path, "w") as f:
        f.write("# GEO × Solar Activity Exploratory Analysis Summary\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

        f.write("## Dataset Overview\n\n")
        f.write(f"- Total GEO Series (iPSC/ESC differentiation): **{len(geo_df)}**\n")
        if len(geo_df) > 0:
            f.write(f"- Date range: {geo_df['date'].min().strftime('%Y-%m')} to "
                    f"{geo_df['date'].max().strftime('%Y-%m')}\n")
            f.write(f"- Northern Hemisphere datasets: "
                    f"**{(geo_df['hemisphere']=='Northern').sum()}**\n")
            f.write(f"- Southern Hemisphere datasets: "
                    f"**{(geo_df['hemisphere']=='Southern').sum()}**\n")
            f.write(f"- Unassigned hemisphere: "
                    f"**{geo_df['hemisphere'].isna().sum()}**\n\n")

            f.write("### Top locations (inferred)\n\n")
            loc_counts = geo_df["loc_keyword"].dropna().value_counts().head(15)
            for loc, cnt in loc_counts.items():
                f.write(f"- {loc}: {cnt}\n")

            f.write("\n### Monthly distribution\n\n")
            f.write("| Month | All | NH | SH |\n")
            f.write("|-------|-----|----|----|  \n")
            for m in range(1, 13):
                month_name = ["Jan","Feb","Mar","Apr","May","Jun",
                             "Jul","Aug","Sep","Oct","Nov","Dec"][m-1]
                all_n = (geo_df["month"] == m).sum()
                nh_n = ((geo_df["month"] == m) & (geo_df["hemisphere"] == "Northern")).sum()
                sh_n = ((geo_df["month"] == m) & (geo_df["hemisphere"] == "Southern")).sum()
                f.write(f"| {month_name} | {all_n} | {nh_n} | {sh_n} |\n")

        f.write("\n## Solar Activity Data\n\n")
        if solar_df is not None and len(solar_df) > 0:
            f.write(f"- NOAA monthly indices: {len(solar_df)} months\n")
            f.write(f"- Date range: {solar_df['date'].min().strftime('%Y-%m')} to "
                    f"{solar_df['date'].max().strftime('%Y-%m')}\n")

        f.write("\n## Figures\n\n")
        f.write("- `analysis1_seasonal_distribution.png`: Monthly/seasonal patterns\n")
        f.write("- `analysis2_solar_correlation.png`: Solar activity correlations\n")

    print(f"\nSummary saved to: {out_path}")
    return out_path


def main():
    print("="*60)
    print("GEO × Solar/Seasonal Exploratory Analysis")
    print("="*60)

    # Step 1: Fetch GEO metadata
    print("\n[Step 1] Fetching GEO metadata...")
    geo_df = fetch_geo_metadata()

    # Cache to CSV
    geo_csv = os.path.join(OUTPUT_DIR, "geo_psc_metadata.csv")
    geo_df.to_csv(geo_csv, index=False)
    print(f"  Cached to: {geo_csv}")

    # Step 2: Fetch NOAA solar indices
    print("\n[Step 2] Fetching NOAA solar indices...")
    solar_df = fetch_noaa_solar_indices()
    solar_csv = os.path.join(OUTPUT_DIR, "noaa_solar_indices.csv")
    solar_df.to_csv(solar_csv, index=False)
    print(f"  Cached to: {solar_csv}")

    # Step 3: Analysis 1 — Seasonal
    print("\n[Step 3] Running seasonal analysis...")
    analysis_seasonal(geo_df)

    # Step 4: Analysis 2 — Solar correlation
    print("\n[Step 4] Running solar correlation analysis...")
    analysis_solar(geo_df, solar_df)

    # Step 5: Summary report
    print("\n[Step 5] Generating summary report...")
    save_summary_report(geo_df, solar_df)

    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
