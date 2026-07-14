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


def _norm_country(s):
    s = str(s).strip().lower()
    repl = {
        'united states of america': 'united states', 'usa': 'united states',
        'united states': 'united states', 'russian federation': 'russia',
        'korea, rep.': 'south korea', 'korea, dem. people\u2019s rep.': 'north korea',
        'south korea': 'south korea', 'egypt, arab rep.': 'egypt',
        'iran, islamic rep.': 'iran', 'venezuela, rb': 'venezuela',
        'turkiye': 'turkey', 't\u00fcrkiye': 'turkey', 'czechia': 'czech republic',
        'slovak republic': 'slovakia', 'kyrgyz republic': 'kyrgyzstan',
        'lao pdr': 'laos', 'brunei darussalam': 'brunei',
        'congo, dem. rep.': 'democratic republic of the congo',
        'congo, rep.': 'republic of the congo', 'gambia, the': 'gambia',
        'bahamas, the': 'bahamas', 'yemen, rep.': 'yemen',
        'syrian arab republic': 'syria', 'viet nam': 'vietnam',
        'hong kong sar, china': 'hong kong', 'cote d\u2019ivoire': "cote d'ivoire",
        "c\u00f4te d'ivoire": "cote d'ivoire", 'cabo verde': 'cape verde',
    }
    return repl.get(s, s)


def fetch_omran():
    """#19 Omran Epidemiological Transition: HDI (development) vs NCD share.

    x: UNDP Human Development Index (latest); y: World Bank WDI cause-of-death
    by non-communicable diseases (% of total, SH.DTH.NCOM.ZS).
    """
    import wbgapi as wb
    hdr = requests.get(
        'https://hdr.undp.org/sites/default/files/2023-24_HDR/'
        'HDR23-24_Composite_indices_complete_time_series.csv',
        timeout=TIMEOUT, headers=HEADERS)
    hdr.raise_for_status()
    hdi = pd.read_csv(io.BytesIO(hdr.content), encoding='latin-1')
    hdi_col = next((c for c in ['hdi_2022', 'hdi_2021'] if c in hdi.columns), None)
    hdi = hdi[['iso3', 'country', hdi_col]].rename(columns={hdi_col: 'hdi'}).dropna()
    for yr in range(2021, 2014, -1):
        try:
            ncd = wb.data.DataFrame('SH.DTH.NCOM.ZS', time=yr, labels=True,
                                    skipBlanks=True)
        except Exception:
            continue
        ncd = ncd.rename(columns={ncd.columns[-1]: 'ncd_share'})
        ncd = ncd.reset_index().rename(columns={'economy': 'iso3'})
        ncd = ncd[['iso3', 'ncd_share']].dropna()
        df = hdi.merge(ncd, on='iso3', how='inner')
        if len(df) >= 50:
            df['ncd_year'] = yr
            return _save(df, 'omran_real.csv')
    raise RuntimeError("Omran: insufficient HDI/NCD overlap")


def fetch_lipset():
    """#44 Lipset Hypothesis: GDP per capita vs democracy level.

    x: World Bank WDI GDP per capita PPP (NY.GDP.PCAP.PP.KD, latest);
    y: Freedom House Freedom in the World aggregate score (Total/100).
    """
    import wbgapi as wb
    fh = requests.get(
        'https://freedomhouse.org/sites/default/files/2024-02/'
        'Aggregate_Category_and_Subcategory_Scores_FIW_2003-2024.xlsx',
        timeout=TIMEOUT, headers=HEADERS)
    fh.raise_for_status()
    fdf = pd.read_excel(io.BytesIO(fh.content), sheet_name='FIW06-24')
    fdf = fdf[fdf['C/T?'] == 'c'] if 'C/T?' in fdf.columns else fdf
    latest = fdf['Edition'].max()
    fdf = fdf[fdf['Edition'] == latest][['Country/Territory', 'Total']].dropna()
    fdf['key'] = fdf['Country/Territory'].map(_norm_country)
    fdf['democracy'] = fdf['Total'] / 100.0

    for yr in range(2022, 2016, -1):
        try:
            gdp = wb.data.DataFrame('NY.GDP.PCAP.PP.KD', time=yr, labels=True,
                                    skipBlanks=True)
        except Exception:
            continue
        gdp = gdp.rename(columns={'NY.GDP.PCAP.PP.KD': 'gdp_pc_ppp'})
        gdp = gdp.reset_index().rename(columns={'economy': 'iso3'})
        gdp = gdp[['iso3', 'Country', 'gdp_pc_ppp']].dropna()
        gdp['key'] = gdp['Country'].map(_norm_country)
        df = gdp.merge(fdf[['key', 'democracy', 'Country/Territory']], on='key',
                       how='inner')
        df = df[['Country', 'iso3', 'gdp_pc_ppp', 'democracy']].dropna()
        if len(df) >= 50:
            df['gdp_year'] = yr
            df['fh_edition'] = int(latest)
            return _save(df, 'lipset_real.csv')
    raise RuntimeError("Lipset: insufficient GDP/Freedom House overlap")


def _eia_total_energy(msn):
    """Fetch an annual EIA Total Energy series (MSN code) as a year->value dict."""
    key = os.environ.get('EIA_API_KEY')
    if not key:
        raise RuntimeError("EIA_API_KEY not set")
    r = requests.get('https://api.eia.gov/v2/total-energy/data/', timeout=TIMEOUT,
                     headers=HEADERS, params={
                         'api_key': key, 'frequency': 'annual', 'data[0]': 'value',
                         'facets[msn][]': msn, 'length': 5000})
    r.raise_for_status()
    rows = r.json()['response']['data']
    out = {}
    for d in rows:
        try:
            out[int(d['period'])] = float(d['value'])
        except (ValueError, TypeError):
            continue
    return out


def fetch_hubbert():
    """#30 Hubbert Peak Oil: Year vs US crude oil production.

    Source: EIA Total Energy, MSN=PAPRPUS (Crude Oil Production, Total,
    thousand barrels/day), annual.
    """
    prod = _eia_total_energy('PAPRPUS')
    df = pd.DataFrame(sorted(prod.items()), columns=['year', 'production_kbd'])
    df = df[df['production_kbd'] > 0]
    return _save(df, 'hubbert_real.csv')


def fetch_jevons():
    """#33 Jevons Paradox: US energy intensity vs total energy consumption.

    Consumption: EIA Total Energy MSN=TETCBUS (Trillion Btu, annual).
    Intensity: consumption / US real GDP (World Bank WDI NY.GDP.MKTP.KD, USA).
    """
    import wbgapi as wb
    cons = _eia_total_energy('TETCBUS')
    gdp = wb.data.DataFrame('NY.GDP.MKTP.KD', economy='USA', labels=False)
    # columns like 'YR1990'
    gdp_by_year = {}
    for col in gdp.columns:
        yr = int(''.join(ch for ch in col if ch.isdigit()))
        val = gdp.iloc[0][col]
        if pd.notna(val):
            gdp_by_year[yr] = float(val)
    rows = []
    for yr in sorted(set(cons) & set(gdp_by_year)):
        c = cons[yr]
        g = gdp_by_year[yr]
        if c > 0 and g > 0:
            # Btu per constant dollar: (Trillion Btu * 1e12) / GDP($)
            rows.append({'year': yr, 'total_energy_tbtu': c,
                         'gdp_real_usd': g,
                         'intensity_btu_per_usd': (c * 1e12) / g})
    df = pd.DataFrame(rows)
    if len(df) < 10:
        raise RuntimeError("Jevons: insufficient EIA/WDI overlap")
    return _save(df, 'jevons_real.csv')


def _bls_series(series_ids, start_year, end_year):
    """Fetch BLS series (annual averages of monthly data) as
    {series_id: {year: mean_value}}. Splits into <=20-year windows."""
    key = os.environ.get('BLS_API_KEY')
    if not key:
        raise RuntimeError("BLS_API_KEY not set")
    from collections import defaultdict
    acc = {sid: defaultdict(list) for sid in series_ids}
    y0 = start_year
    while y0 <= end_year:
        y1 = min(y0 + 19, end_year)
        r = requests.post(
            'https://api.bls.gov/publicAPI/v2/timeseries/data/',
            json={'seriesid': series_ids, 'startyear': str(y0),
                  'endyear': str(y1), 'registrationkey': key},
            timeout=TIMEOUT, headers=HEADERS)
        r.raise_for_status()
        js = r.json()
        if js.get('status') != 'REQUEST_SUCCEEDED':
            raise RuntimeError(f"BLS error: {js.get('message')}")
        for s in js['Results']['series']:
            sid = s['seriesID']
            for d in s['data']:
                if d['period'].startswith('M'):
                    acc[sid][int(d['year'])].append(float(d['value']))
        y0 = y1 + 1
    return {sid: {yr: sum(v) / len(v) for yr, v in yrs.items()}
            for sid, yrs in acc.items()}


def fetch_beveridge():
    """#5 Beveridge Curve: US unemployment rate vs job-openings (vacancy) rate.

    Source: BLS API. Unemployment rate LNS14000000 (CPS, SA); job openings
    rate JTS000000000000000JOR (JOLTS total nonfarm, SA). Annual averages.
    """
    unemp_id = 'LNS14000000'
    vac_id = 'JTS000000000000000JOR'
    data = _bls_series([unemp_id, vac_id], 2001, 2024)
    rows = []
    for yr in sorted(set(data[unemp_id]) & set(data[vac_id])):
        rows.append({'year': yr,
                     'unemployment_rate': round(data[unemp_id][yr], 3),
                     'vacancy_rate': round(data[vac_id][yr], 3)})
    df = pd.DataFrame(rows)
    if len(df) < 10:
        raise RuntimeError("Beveridge: insufficient BLS overlap")
    return _save(df, 'beveridge_real.csv')


FETCHERS = {
    'ekc_co2': fetch_ekc_co2,
    'keeling': fetch_keeling,
    'gutenberg_richter': fetch_gutenberg_richter,
    'moores_law': fetch_moores_law,
    'balassa_samuelson': fetch_balassa_samuelson,
    'omran': fetch_omran,
    'lipset': fetch_lipset,
    'hubbert': fetch_hubbert,
    'jevons': fetch_jevons,
    'beveridge': fetch_beveridge,
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
