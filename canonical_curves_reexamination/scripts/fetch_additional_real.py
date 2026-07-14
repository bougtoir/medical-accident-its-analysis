"""
Fetch additional real datasets for canonical curves that were previously
hard-coded, and save them as CSVs under ../data/.

Each fetcher pulls from a public, third-party-traceable source:
  - Environmental Kuznets Curve (CO2, #4): World Bank WDI cross-section
  - Keeling Curve (#31): NOAA GML Mauna Loa annual mean CO2
  - Gutenberg-Richter Law (#42): USGS FDSN earthquake catalog (ComCat)
  - Moore's Law (#43): Karl Rupp microprocessor-trend-data (transistor counts)
  - Balassa-Samuelson (#12): Penn World Table 10.01

Run:  python fetch_additional_real.py
Outputs are consumed by data_additional_real.py during run_all_analyses.py.
"""

import io
import os
import sys

import numpy as np
import pandas as pd
import requests

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
TIMEOUT = 60
HEADERS = {"User-Agent": "canonical-curves-reexamination/1.0 (research reproducibility)"}


def _save(df, fname):
    path = os.path.join(DATA_DIR, fname)
    df.to_csv(path, index=False)
    print(f"  saved {fname} ({len(df)} rows)")
    return path


def fetch_ekc_co2():
    """#4 Environmental Kuznets Curve: GDP per capita PPP vs CO2 per capita.

    Source: World Bank WDI (NY.GDP.PCAP.PP.KD, EN.GHG.CO2.PC.CE.AR5), most
    recent year with joint coverage.
    """
    import wbgapi as wb
    # CO2 per capita indicator (EN.ATM.CO2E.PC was archived; use EN.GHG.CO2.PC.* fallback chain)
    co2_candidates = ['EN.GHG.CO2.PC.CE.AR5', 'EN.ATM.CO2E.PC']
    gdp_code = 'NY.GDP.PCAP.PP.KD'
    for yr in range(2022, 2016, -1):
        for co2_code in co2_candidates:
            try:
                gdp = wb.data.DataFrame(gdp_code, time=yr, labels=True, skipBlanks=True)
                co2 = wb.data.DataFrame(co2_code, time=yr, labels=True, skipBlanks=True)
            except Exception:
                continue
            gdp = gdp.rename(columns={gdp.columns[-1]: 'gdp_pc_ppp'})
            co2 = co2.rename(columns={co2.columns[-1]: 'co2_pc'})
            df = gdp[['Country', 'gdp_pc_ppp']].join(co2['co2_pc'], how='inner')
            df = df.reset_index().rename(columns={'economy': 'country_code', 'Country': 'country'})
            df = df.dropna(subset=['gdp_pc_ppp', 'co2_pc'])
            if len(df) >= 50:
                df['year'] = yr
                df['co2_indicator'] = co2_code
                return _save(df, 'ekc_co2_real.csv')
    raise RuntimeError("EKC CO2: no year with joint GDP/CO2 coverage found")


def fetch_keeling():
    """#31 Keeling Curve: year vs atmospheric CO2 (Mauna Loa annual means)."""
    url = 'https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_annmean_mlo.csv'
    r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
    r.raise_for_status()
    lines = [ln for ln in r.text.splitlines() if not ln.startswith('#')]
    df = pd.read_csv(io.StringIO('\n'.join(lines)))
    df = df.rename(columns={'mean': 'co2_ppm'})[['year', 'co2_ppm']].dropna()
    return _save(df, 'keeling_real.csv')


def fetch_gutenberg_richter():
    """#42 Gutenberg-Richter: magnitude vs annual global earthquake frequency.

    Counts events at/above each magnitude threshold from the USGS FDSN event
    service over a fixed multi-year window, then converts to annual rate.
    """
    start, end = '2000-01-01', '2020-01-01'
    years = 20.0
    mags = np.arange(4.0, 8.6, 0.5)
    rows = []
    for m in mags:
        url = ('https://earthquake.usgs.gov/fdsnws/event/1/count'
               f'?format=text&starttime={start}&endtime={end}&minmagnitude={m:.1f}')
        r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
        r.raise_for_status()
        count = int(r.text.strip())
        rows.append({'magnitude': m, 'count_total': count,
                     'annual_count': count / years})
    df = pd.DataFrame(rows)
    df = df[df['annual_count'] > 0]
    df['window_start'] = start
    df['window_end'] = end
    return _save(df, 'gutenberg_richter_real.csv')


def fetch_moores_law():
    """#43 Moore's Law: year vs transistor count (Karl Rupp dataset)."""
    url = 'https://raw.githubusercontent.com/karlrupp/microprocessor-trend-data/master/50yrs/transistors.dat'
    r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
    r.raise_for_status()
    rows = []
    for ln in r.text.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith('#'):
            continue
        parts = ln.split()
        if len(parts) >= 2:
            try:
                rows.append({'year': float(parts[0]),
                             'transistors_thousands': float(parts[1])})
            except ValueError:
                continue
    df = pd.DataFrame(rows).dropna()
    return _save(df, 'moores_law_real.csv')


def fetch_balassa_samuelson():
    """#12 Balassa-Samuelson: relative productivity vs relative price level.

    Penn World Table 10.01: labour productivity (rgdpo/emp) and price level of
    output (pl_gdpo), latest year, expressed relative to the USA.
    """
    url = 'https://www.rug.nl/ggdc/docs/pwt100.xlsx'
    r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
    r.raise_for_status()
    xls = pd.ExcelFile(io.BytesIO(r.content))
    sheet = 'Data' if 'Data' in xls.sheet_names else xls.sheet_names[-1]
    df = xls.parse(sheet)
    yr = int(df['year'].max())
    while yr > df['year'].max() - 6:
        sub = df[df['year'] == yr].copy()
        sub['productivity'] = sub['rgdpo'] / sub['emp']
        sub = sub.dropna(subset=['productivity', 'pl_gdpo'])
        us = sub[sub['countrycode'] == 'USA']
        if len(us) and len(sub) >= 30:
            us_prod = us['productivity'].iloc[0]
            us_pl = us['pl_gdpo'].iloc[0]
            out = pd.DataFrame({
                'country': sub['country'],
                'country_code': sub['countrycode'],
                'productivity_rel_us': 100.0 * sub['productivity'] / us_prod,
                'price_level_rel_us': sub['pl_gdpo'] / us_pl,
                'year': yr,
            })
            return _save(out, 'balassa_samuelson_real.csv')
        yr -= 1
    raise RuntimeError("Balassa-Samuelson: insufficient PWT coverage")


FETCHERS = {
    'ekc_co2': fetch_ekc_co2,
    'keeling': fetch_keeling,
    'gutenberg_richter': fetch_gutenberg_richter,
    'moores_law': fetch_moores_law,
    'balassa_samuelson': fetch_balassa_samuelson,
}


def main(selected=None):
    print(f"Fetching additional real data into {DATA_DIR}")
    ok, fail = [], []
    for key, fn in FETCHERS.items():
        if selected and key not in selected:
            continue
        try:
            print(f"[{key}]")
            fn()
            ok.append(key)
        except Exception as e:
            print(f"  FAILED {key}: {e}")
            fail.append(key)
    print(f"\nDone. ok={ok} failed={fail}")
    return ok, fail


if __name__ == '__main__':
    args = sys.argv[1:] or None
    main(args)
