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
    {series_id: {year: mean_value}}.

    Uses the v2 API when BLS_API_KEY is set and valid (<=20-year windows),
    otherwise falls back to the keyless v1 API (<=10-year windows).
    """
    from collections import defaultdict
    key = os.environ.get('BLS_API_KEY')

    def _request(url, y0, y1, payload):
        r = requests.post(url, json=payload, timeout=TIMEOUT, headers=HEADERS)
        r.raise_for_status()
        return r.json()

    use_v2 = bool(key)
    if use_v2:  # probe key validity on the first window
        probe = _request('https://api.bls.gov/publicAPI/v2/timeseries/data/',
                         start_year, start_year,
                         {'seriesid': series_ids, 'startyear': str(start_year),
                          'endyear': str(start_year), 'registrationkey': key})
        if probe.get('status') != 'REQUEST_SUCCEEDED':
            print(f"  [BLS] v2 key rejected ({probe.get('message')}); "
                  f"falling back to keyless v1 API")
            use_v2 = False

    url = ('https://api.bls.gov/publicAPI/v2/timeseries/data/' if use_v2
           else 'https://api.bls.gov/publicAPI/v1/timeseries/data/')
    window = 19 if use_v2 else 9

    acc = {sid: defaultdict(list) for sid in series_ids}
    y0 = start_year
    while y0 <= end_year:
        y1 = min(y0 + window, end_year)
        payload = {'seriesid': series_ids, 'startyear': str(y0), 'endyear': str(y1)}
        if use_v2:
            payload['registrationkey'] = key
        js = _request(url, y0, y1, payload)
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


def fetch_zipf(top_n=100):
    """#46 Zipf's Law (US cities): rank vs population.

    Source: US Census Bureau 2020 Decennial (dec/pl), total population
    (P1_001N) of all incorporated places, ranked descending.
    """
    key = os.environ.get('CENSUS_API_KEY')
    if not key:
        raise RuntimeError("CENSUS_API_KEY not set")
    r = requests.get('https://api.census.gov/data/2020/dec/pl', timeout=TIMEOUT,
                     headers=HEADERS, params={
                         'get': 'NAME,P1_001N', 'for': 'place:*',
                         'in': 'state:*', 'key': key})
    if not r.text.lstrip().startswith('['):
        raise RuntimeError(f"Census API rejected request: {r.text[:80]}")
    rows = r.json()[1:]
    places = [(row[0], int(row[1])) for row in rows if row[1] not in (None, '')]
    places.sort(key=lambda x: -x[1])
    places = places[:top_n]
    df = pd.DataFrame({
        'rank': range(1, len(places) + 1),
        'name': [p[0] for p in places],
        'population': [p[1] for p in places],
    })
    return _save(df, 'zipf_cities_real.csv')


def fetch_lee_carter(max_age=99):
    """#25 Lee-Carter: year vs mortality time index kappa_t.

    Estimated by Lee-Carter SVD from Human Mortality Database (HMD) USA period
    death rates (Mx_1x1). Because HMD prohibits redistribution of its raw data,
    the input file is read locally (env HMD_MX_FILE, else data/hmd/USA.Mx_1x1.txt)
    and NOT committed; only the derived kappa_t index is saved.
    """
    src = os.environ.get('HMD_MX_FILE',
                         os.path.join(DATA_DIR, 'hmd', 'USA.Mx_1x1.txt'))
    if not os.path.exists(src):
        raise RuntimeError(
            f"HMD Mx file not found at {src}; download USA period death rates "
            "(Mx_1x1) from mortality.org (free account) and place it there")
    # HMD format: header line + column names, then Year Age Female Male Total
    df = pd.read_csv(src, skiprows=2, sep=r'\s+',
                     names=['Year', 'Age', 'Female', 'Male', 'Total'],
                     na_values=['.'])
    df['Age'] = df['Age'].astype(str).str.replace('+', '', regex=False)
    df = df[df['Age'].str.isdigit()]
    df['Age'] = df['Age'].astype(int)
    df = df[df['Age'] <= max_age]
    df['Total'] = pd.to_numeric(df['Total'], errors='coerce')
    df = df.dropna(subset=['Total'])
    df = df[df['Total'] > 0]
    # matrix log(m): rows=age, cols=year
    mat = df.pivot(index='Age', columns='Year', values='Total').sort_index()
    mat = mat.dropna(axis=1)  # keep years with complete age coverage
    logm = np.log(mat.values)
    ax = logm.mean(axis=1, keepdims=True)
    centered = logm - ax
    U, S, Vt = np.linalg.svd(centered, full_matrices=False)
    bx = U[:, 0]
    kt = S[0] * Vt[0, :]
    # Lee-Carter identification: sum(bx)=1
    s = bx.sum()
    bx, kt = bx / s, kt * s
    years = mat.columns.values.astype(int)
    # sign convention: mortality improves over time -> kappa_t decreasing
    if kt[-1] > kt[0]:
        kt = -kt
    out = pd.DataFrame({'year': years, 'kappa_t': kt})
    return _save(out, 'lee_carter_real.csv')


def fetch_easterlin():
    """#14 Easterlin Paradox: GDP per capita vs subjective well-being (cross-section).

    Happiness: Our World in Data 'happiness-cantril-ladder' (Cantril ladder,
    sourced from the World Happiness Report / Gallup World Poll), key-free CSV.
    Income: World Bank WDI GDP per capita, PPP constant (NY.GDP.PCAP.PP.KD).
    Matched by ISO3 country code on each country's most recent common year.
    """
    import wbgapi as wb
    url = ('https://ourworldindata.org/grapher/happiness-cantril-ladder.csv'
           '?v=1&csvType=full')
    r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
    r.raise_for_status()
    from io import StringIO
    hap = pd.read_csv(StringIO(r.text))
    hap.columns = ['entity', 'code', 'year', 'ladder']
    hap = hap.dropna(subset=['code', 'ladder'])
    hap = hap[hap['code'].str.len() == 3]  # drop aggregates (e.g. 'OWID_*')

    gdp = wb.data.DataFrame('NY.GDP.PCAP.PP.KD', time=range(2010, 2024),
                            labels=False)
    # index=economy (ISO3), columns like 'YR2020'
    gdp_long = {}
    for iso3, row in gdp.iterrows():
        for col, val in row.items():
            if pd.notna(val):
                yr = int(''.join(ch for ch in col if ch.isdigit()))
                gdp_long[(iso3, yr)] = float(val)

    rows = []
    for code, g in hap.groupby('code'):
        g = g.sort_values('year')
        for _, rec in g[::-1].iterrows():  # most recent first
            yr = int(rec['year'])
            key = (code, yr)
            if key in gdp_long:
                rows.append({'country': rec['entity'], 'iso3': code,
                             'year': yr, 'gdp_pc_ppp': gdp_long[key],
                             'happiness': float(rec['ladder'])})
                break
    df = pd.DataFrame(rows)
    df = df[df['gdp_pc_ppp'] > 0]
    if len(df) < 30:
        raise RuntimeError("Easterlin: insufficient OWID/WDI overlap")
    return _save(df, 'easterlin_real.csv')


def _owid_csv(slug):
    url = f'https://ourworldindata.org/grapher/{slug}.csv?v=1&csvType=full'
    r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
    r.raise_for_status()
    from io import StringIO
    df = pd.read_csv(StringIO(r.text))
    return df[df['Code'].notna() & (df['Code'].str.len() == 3)]


def _wdi_latest_by_iso3(indicator, years):
    """Return {iso3: {year: value}} for a WDI indicator over a year range."""
    import wbgapi as wb
    df = wb.data.DataFrame(indicator, time=years, labels=False)
    out = {}
    for iso3, row in df.iterrows():
        for col, val in row.items():
            if pd.notna(val):
                yr = int(''.join(ch for ch in col if ch.isdigit()))
                out.setdefault(iso3, {})[yr] = float(val)
    return out


def fetch_engel():
    """#7 Engel Curve: GDP per capita vs food expenditure share (cross-section).

    Food share: OWID 'share-of-consumer-expenditure-spent-on-food' (USDA ERS).
    Income: World Bank WDI GDP per capita PPP (NY.GDP.PCAP.PP.KD).
    Matched by ISO3 on each country's most recent common year.
    """
    food = _owid_csv('share-of-consumer-expenditure-spent-on-food')
    food.columns = list(food.columns[:3]) + ['food_share']
    gdp = _wdi_latest_by_iso3('NY.GDP.PCAP.PP.KD', range(2010, 2024))
    rows = []
    for code, g in food.groupby('Code'):
        for _, rec in g.sort_values('Year')[::-1].iterrows():
            yr = int(rec['Year'])
            if code in gdp and yr in gdp[code]:
                rows.append({'country': rec['Entity'], 'iso3': code, 'year': yr,
                             'gdp_pc_ppp': gdp[code][yr],
                             'food_share': float(rec['food_share'])})
                break
    df = pd.DataFrame(rows)
    df = df[(df['gdp_pc_ppp'] > 0) & (df['food_share'] > 0)]
    if len(df) < 30:
        raise RuntimeError("Engel: insufficient OWID/WDI overlap")
    return _save(df, 'engel_real.csv')


def fetch_rahn():
    """#9 Rahn Curve: government size vs economic growth (cross-section).

    Government expenditure (% GDP): OWID 'historical-gov-spending-gdp'
    (IMF general government total expenditure), decade mean 2010-2019.
    Growth: World Bank WDI real GDP growth (NY.GDP.MKTP.KD.ZG), same window.
    Matched by ISO3.
    """
    gov = _owid_csv('historical-gov-spending-gdp')
    gov.columns = list(gov.columns[:3]) + list(gov.columns[3:])
    gov_col = [c for c in gov.columns if 'expenditure' in c.lower()][0]
    gov = gov[(gov['Year'] >= 2010) & (gov['Year'] <= 2019)]
    gov_mean = gov.groupby(['Code', 'Entity'])[gov_col].mean().reset_index()
    growth = _wdi_latest_by_iso3('NY.GDP.MKTP.KD.ZG', range(2010, 2020))
    rows = []
    for _, rec in gov_mean.iterrows():
        code = rec['Code']
        if code in growth and growth[code]:
            g = np.mean(list(growth[code].values()))
            rows.append({'country': rec['Entity'], 'iso3': code,
                         'gov_expenditure_gdp': float(rec[gov_col]),
                         'gdp_growth': float(g)})
    df = pd.DataFrame(rows)
    df = df[df['gov_expenditure_gdp'] > 0]
    if len(df) < 30:
        raise RuntimeError("Rahn: insufficient OWID/WDI overlap")
    return _save(df, 'rahn_real.csv')


def fetch_species_area():
    """#29 Species-Area: Galapagos island area vs plant species count.

    Source: Johnson & Raven (1973) Science 179:893-895, distributed as the
    'gala' dataset in the R 'faraway' package. Downloads the CRAN source tarball
    and reads data/gala.rda (raw tarball cached under data/cache/, gitignored).
    """
    import tarfile
    import pyreadr
    cache = os.path.join(DATA_DIR, 'cache')
    os.makedirs(cache, exist_ok=True)
    tpath = os.path.join(cache, 'faraway_source.tar.gz')
    if not os.path.exists(tpath):
        url = 'https://cran.r-project.org/src/contrib/faraway_1.0.9.tar.gz'
        with requests.get(url, timeout=TIMEOUT, headers=HEADERS,
                          stream=True) as r:
            r.raise_for_status()
            with open(tpath, 'wb') as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
    with tarfile.open(tpath) as tf:
        tf.extract('faraway/data/gala.rda', cache)
    rda = pyreadr.read_r(os.path.join(cache, 'faraway', 'data', 'gala.rda'))
    df = rda['gala'].reset_index().rename(columns={'index': 'island',
                                                   'rownames': 'island'})
    df = df[['island', 'Area', 'Species']]
    if len(df) < 20:
        raise RuntimeError("Species-Area: unexpected row count")
    return _save(df, 'species_area_real.csv')


def fetch_kleiber():
    """#41 Kleiber's Law: mammal body mass vs basal metabolic rate.

    Source: AnAge database (Human Ageing Genomic Resources; Tacutu et al. 2018
    Nucleic Acids Res). Restricted to Class Mammalia with metabolic rate (W)
    and body mass (g) both present. Raw zip cached under data/cache/ (gitignored).
    """
    import zipfile
    cache = os.path.join(DATA_DIR, 'cache')
    os.makedirs(cache, exist_ok=True)
    zpath = os.path.join(cache, 'anage_dataset.zip')
    if not os.path.exists(zpath):
        url = 'https://genomics.senescence.info/species/dataset.zip'
        with requests.get(url, timeout=TIMEOUT, headers=HEADERS) as r:
            r.raise_for_status()
            with open(zpath, 'wb') as f:
                f.write(r.content)
    with zipfile.ZipFile(zpath) as z:
        df = pd.read_csv(io.BytesIO(z.read('anage_data.txt')), sep='\t')
    df = df[df['Class'] == 'Mammalia'].dropna(
        subset=['Metabolic rate (W)', 'Body mass (g)'])
    df = df[(df['Metabolic rate (W)'] > 0) & (df['Body mass (g)'] > 0)].copy()
    df['species'] = df['Genus'].astype(str) + ' ' + df['Species'].astype(str)
    df['body_mass_kg'] = df['Body mass (g)'] / 1000.0
    df['bmr_watts'] = df['Metabolic rate (W)']
    out = df[['species', 'body_mass_kg', 'bmr_watts']].sort_values(
        'body_mass_kg')
    if len(out) < 100:
        raise RuntimeError("Kleiber: unexpected row count")
    return _save(out, 'kleiber_real.csv')


def fetch_duverger():
    """#45 Duverger's Law: district magnitude vs effective number of parties.

    Source: Bormann & Golder, Democratic Electoral Systems (DES) 5.0
    (Electoral Studies 2022; Open Research Europe 2024). Legislative elections
    with tier-1 average district magnitude and effective number of electoral
    parties (enep). Raw zip cached under data/cache/ (gitignored).
    """
    import zipfile
    cache = os.path.join(DATA_DIR, 'cache')
    os.makedirs(cache, exist_ok=True)
    zpath = os.path.join(cache, 'des_v50.zip')
    if not os.path.exists(zpath):
        url = 'https://mattgolder.com/files/research/es_data-v50.zip'
        with requests.get(url, timeout=TIMEOUT, headers=HEADERS) as r:
            r.raise_for_status()
            with open(zpath, 'wb') as f:
                f.write(r.content)
    with zipfile.ZipFile(zpath) as z:
        name = [n for n in z.namelist()
                if n.endswith('.csv') and not n.startswith('__MACOSX')][0]
        df = pd.read_csv(io.BytesIO(z.read(name)), low_memory=False)
    df = df.dropna(subset=['tier1_avemag', 'enep', 'legislative_type'])
    df = df[(df['tier1_avemag'] > 0) & (df['enep'] > 0)].copy()
    out = df[['country', 'year', 'tier1_avemag', 'enep']].rename(
        columns={'tier1_avemag': 'district_magnitude'})
    if len(out) < 100:
        raise RuntimeError("Duverger: unexpected row count")
    return _save(out, 'duverger_real.csv')


def fetch_gravity(year=2019):
    """#10 Gravity Model of Trade: gravity index vs bilateral trade.

    Source: CEPII Gravity database V202211 (Conte, Cotterlaz & Mayer 2022).
    For a given year, keeps ordered country pairs (o<d) with valid origin/
    destination GDP (gdp_o, gdp_d), bilateral distance (dist) and BACI bilateral
    trade (tradeflow_baci > 0). Raw archive (~1.2 GB) is cached under
    data/cache/ (gitignored); only the filtered pairs are saved.
    """
    import zipfile
    import csv
    cache = os.path.join(DATA_DIR, 'cache')
    os.makedirs(cache, exist_ok=True)
    zpath = os.path.join(cache, 'cepii_gravity_V202211.zip')
    if not os.path.exists(zpath):
        url = ('https://www.cepii.fr/DATA_DOWNLOAD/gravity/data/'
               'Gravity_csv_V202211.zip')
        with requests.get(url, timeout=TIMEOUT, headers=HEADERS,
                          stream=True) as r:
            r.raise_for_status()
            with open(zpath, 'wb') as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
    with zipfile.ZipFile(zpath) as z:
        name = [n for n in z.namelist() if n.startswith('Gravity_')][0]
        rows = []
        with z.open(name) as fh:
            reader = csv.reader(
                (line.decode('utf-8') for line in fh))
            header = next(reader)
            idx = {c.strip('"'): i for i, c in enumerate(header)}
            iy, io, id_ = idx['year'], idx['iso3_o'], idx['iso3_d']
            ig_o, ig_d = idx['gdp_o'], idx['gdp_d']
            idist, itr = idx['dist'], idx['tradeflow_baci']
            for row in reader:
                if row[iy] != str(year):
                    continue
                o, d = row[io].strip('"'), row[id_].strip('"')
                if o >= d:
                    continue
                try:
                    go, gd = float(row[ig_o]), float(row[ig_d])
                    dist, tr = float(row[idist]), float(row[itr])
                except ValueError:
                    continue
                if go > 0 and gd > 0 and dist > 0 and tr > 0:
                    rows.append({'iso3_o': o, 'iso3_d': d, 'gdp_o': go,
                                 'gdp_d': gd, 'dist': dist,
                                 'tradeflow_baci': tr})
    df = pd.DataFrame(rows)
    if len(df) < 100:
        raise RuntimeError("Gravity: unexpected row count")
    return _save(df, 'gravity_real.csv')


def fetch_hubble():
    """#40 Hubble's Law: distance vs recession velocity (original 1929 data).

    Hubble E (1929) PNAS 15(3):168-173, Table 1 (24 extra-galactic nebulae),
    public domain. Machine-readable transcription fetched from a public mirror;
    values are the original published distances (Mpc) and velocities (km/s).
    """
    url = ('https://raw.githubusercontent.com/behrouzz/astrodatascience/'
           'main/data/hubble1929.csv')
    r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
    r.raise_for_status()
    from io import StringIO
    df = pd.read_csv(StringIO(r.text))
    df.columns = ['object', 'distance_mpc', 'velocity_kms']
    df = df.dropna(subset=['distance_mpc', 'velocity_kms'])
    if len(df) < 20:
        raise RuntimeError("Hubble: unexpected row count")
    return _save(df, 'hubble_real.csv')


def fetch_laffer():
    """#2 Laffer Curve: top marginal personal income tax rate vs tax revenue.

    Two OECD sources, latest available year per country (2015-2023):
      - x = top (statutory) personal income tax rate, OECD Tax Database
        Table I.7 (series TAX=PERS_ITAX, combined central + sub-central),
        via the OECD SDMX-JSON legacy endpoint.
      - y = total tax revenue as % of GDP, OECD Global Revenue Statistics
        (dataflow DSD_REV_COMP_GLOBAL@DF_RSGLOBAL: MEASURE=TAX_REV,
        SECTOR=S13 general government, STANDARD_REVENUE=_T total,
        UNIT_MEASURE=PT_B1GQ % of GDP), via the OECD Data Explorer SDMX API.
    Countries are matched on ISO3. Both source responses are cached under
    data/cache/ (gitignored). The per-country reference year is recorded so
    every point is traceable.
    """
    import csv as _csv
    cache = os.path.join(DATA_DIR, 'cache')
    os.makedirs(cache, exist_ok=True)

    # --- x: top personal income tax rate (OECD Table I.7, PERS_ITAX) ---
    ratepath = os.path.join(cache, 'oecd_table_i7_pers_itax.json')
    if not os.path.exists(ratepath):
        u = ('https://stats.oecd.org/SDMX-JSON/data/TABLE_I7/.PERS_ITAX/all'
             '?startTime=2015&endTime=2024')
        r = requests.get(u, timeout=TIMEOUT * 2, headers=HEADERS)
        r.raise_for_status()
        with open(ratepath, 'w') as f:
            f.write(r.text)
    import json as _json
    with open(ratepath) as f:
        d = _json.load(f)
    st = d['data']['structures'][0]
    sdims = st['dimensions']['series']
    tp = [v['id'] for v in st['dimensions']['observation'][0]['values']]
    rate = {}  # (iso, year) -> top rate
    for k, v in d['data']['dataSets'][0]['series'].items():
        c = {sdims[i]['id']: sdims[i]['values'][int(x)]['id']
             for i, x in enumerate(k.split(':'))}
        if c.get('TAX') != 'PERS_ITAX':
            continue
        for oi, ov in v['observations'].items():
            if ov[0] is not None and float(ov[0]) > 0:
                rate[(c['COU'], int(tp[int(oi)]))] = float(ov[0])

    # --- y: total tax revenue as % of GDP (OECD Global Revenue Statistics) ---
    revpath = os.path.join(cache, 'oecd_revenue_pct_gdp.csv')
    if not os.path.exists(revpath):
        u = ('https://sdmx.oecd.org/public/rest/data/'
             'OECD.CTP.TPS,DSD_REV_COMP_GLOBAL@DF_RSGLOBAL,2.1/'
             '.TAX_REV.S13._T._T.PT_B1GQ.A'
             '?startPeriod=2015&endPeriod=2024&dimensionAtObservation=AllDimensions')
        r = requests.get(u, timeout=TIMEOUT * 2,
                         headers={**HEADERS,
                                  'Accept': 'application/vnd.sdmx.data+csv'})
        r.raise_for_status()
        with open(revpath, 'w') as f:
            f.write(r.text)
    rev = {}  # (iso, year) -> tax revenue % GDP
    for row in _csv.DictReader(open(revpath)):
        try:
            rev[(row['REF_AREA'], int(row['TIME_PERIOD']))] = float(row['OBS_VALUE'])
        except (KeyError, ValueError):
            continue

    # Single common cross-section year: use the most recent year with broad
    # joint coverage (>=25 countries with BOTH the top PIT rate and tax
    # revenue); fall back to the max-coverage year otherwise.
    isos = {i for i, _ in rate} | {i for i, _ in rev}
    by_year = {yr: [i for i in isos if (i, yr) in rate and (i, yr) in rev]
               for yr in range(2023, 2015, -1)}
    recent = [yr for yr in sorted(by_year, reverse=True) if len(by_year[yr]) >= 25]
    best_year = recent[0] if recent else max(by_year, key=lambda y: len(by_year[y]))
    best_isos = by_year[best_year]
    rows = [{'iso3': i, 'year': best_year,
             'top_rate': round(rate[(i, best_year)], 3),
             'tax_revenue_gdp': round(rev[(i, best_year)], 3)}
            for i in best_isos]
    out = pd.DataFrame(rows).sort_values('top_rate')
    if len(out) < 20:
        raise RuntimeError("Laffer: unexpected row count")
    return _save(out, 'laffer_real.csv')


def fetch_great_gatsby():
    """#11 Great Gatsby Curve: income inequality vs intergenerational (im)mobility.

    Reconstruction (NOT the original Corak 2013 figure), matched on ISO3:
      - y = intergenerational income elasticity (IGE, father-son): World Bank
        Global Database on Intergenerational Mobility (GDIM) income mobility
        dataset (Munoz & van der Weide 2025, WB Policy Research WP 11166),
        file IGE_Munoz_VanderWeide_June2025.dta (87 economies).
      - x = Gini index (income inequality): Our World in Data
        'economic-inequality-gini-index' (World Bank Poverty & Inequality
        Platform), most recent year 2000-2022 per country, rescaled to 0-100.
    Higher IGE = less mobility. The GDIM .dta is cached under data/cache/
    (gitignored). This is a modern public-data reconstruction of the Great
    Gatsby relationship, not a replication of Corak's original point set.
    """
    cache = os.path.join(DATA_DIR, 'cache')
    os.makedirs(cache, exist_ok=True)
    dta = os.path.join(cache, 'gdim_ige_income.dta')
    if not os.path.exists(dta):
        url = ('https://datacatalogfiles.worldbank.org/ddh-published/0066878/'
               'DR0095414/IGE_Munoz_VanderWeide_June2025.dta')
        with requests.get(url, timeout=TIMEOUT * 2, headers=HEADERS) as r:
            r.raise_for_status()
            with open(dta, 'wb') as f:
                f.write(r.content)
    ige = pd.read_stata(dta)
    ige = ige.dropna(subset=['IGE'])
    g = _owid_csv('economic-inequality-gini-index')
    g = g[(g['Year'] >= 2000) & (g['Year'] <= 2022)].dropna(
        subset=['Gini coefficient'])
    gini = {}
    for code, grp in g.groupby('Code'):
        rec = grp.sort_values('Year').iloc[-1]
        val = float(rec['Gini coefficient'])
        gini[code] = (int(rec['Year']), val * 100 if val <= 1 else val)
    rows = []
    for _, rec in ige.iterrows():
        code = rec['code']
        if code in gini:
            yr, val = gini[code]
            rows.append({'iso3': code, 'gini': round(val, 2),
                         'gini_year': yr, 'ige': round(float(rec['IGE']), 4),
                         'ige_source': rec['source']})
    out = pd.DataFrame(rows).sort_values('gini')
    if len(out) < 30:
        raise RuntimeError("Great Gatsby: unexpected row count")
    return _save(out, 'great_gatsby_real.csv')


def fetch_hanpp():
    """#32 HANPP vs development: country HANPP (% of NPP0) vs GDP per capita.

    Haberl et al. (2007) PNAS 104:12942-12947 do not publish a country-level
    HANPP table; they publish gridded HANPP for the year 2000. Country values
    here are computed by ZONAL AGGREGATION of the official Haberl 2007 grids:
      country HANPP% = 100 * sum(HANPP_gCm2 * cell_area) /
                             sum(NPP0_gCm2 * cell_area)
    over the country's land cells (cos-latitude area weighting), using the
    5-arc-minute grids 'thanpppallgcm' (HANPP, gC/m2/yr) and 'tn0_all_gcm'
    (NPP0, gC/m2/yr) from the Global HANPP Data package (all_grids.zip),
    and Natural Earth 1:110m admin-0 country polygons (ISO_A3).
    x = GDP per capita, PPP (OWID / World Bank), year 2000 to match the grid.
    Raw archives are cached under data/cache/ (gitignored).
    """
    import zipfile
    import rasterio
    import geopandas as gpd
    from rasterio.features import rasterize
    cache = os.path.join(DATA_DIR, 'cache')
    os.makedirs(cache, exist_ok=True)

    gz = os.path.join(cache, 'haberl2007_all_grids.zip')
    if not os.path.exists(gz):
        with requests.get('https://seafile.aau.at/f/ae722a88d7/?raw=1',
                          timeout=TIMEOUT * 5, headers=HEADERS) as r:
            r.raise_for_status()
            with open(gz, 'wb') as f:
                f.write(r.content)
    gdir = os.path.join(cache, 'haberl2007_grids')
    if not os.path.isdir(gdir):
        with zipfile.ZipFile(gz) as z:
            z.extractall(gdir)

    nez = os.path.join(cache, 'ne_110m_admin_0_countries.zip')
    if not os.path.exists(nez):
        with requests.get('https://naciscdn.org/naturalearth/110m/cultural/'
                          'ne_110m_admin_0_countries.zip',
                          timeout=TIMEOUT * 2, headers=HEADERS) as r:
            r.raise_for_status()
            with open(nez, 'wb') as f:
                f.write(r.content)

    hg = rasterio.open(os.path.join(gdir, 'thanpppallgcm'))
    ng = rasterio.open(os.path.join(gdir, 'tn0_all_gcm'))
    Hd = hg.read(1).astype('float64')
    Nd = ng.read(1).astype('float64')
    valid = ((Hd != hg.nodata) & (Nd != ng.nodata)
             & np.isfinite(Hd) & np.isfinite(Nd))
    tr = hg.transform
    height, width = hg.height, hg.width
    lat = tr.f + (np.arange(height) + 0.5) * tr.e
    wgrid = np.repeat(np.cos(np.deg2rad(lat))[:, None], width, axis=1)

    g = gpd.read_file(f'zip://{nez}')
    g['iso'] = g['ISO_A3_EH'].where(g['ISO_A3_EH'].str.len() == 3,
                                    g['ADM0_ISO'])
    g = g[(g['iso'].str.len() == 3) & (g['iso'] != '-99')].reset_index(drop=True)
    cid = rasterize([(geom, i + 1) for i, geom in enumerate(g.geometry)],
                    out_shape=(height, width), transform=tr, fill=0,
                    dtype='int32')
    sel = valid & (cid > 0)
    idx = cid[sel]
    num = np.bincount(idx, weights=(Hd * wgrid)[sel], minlength=len(g) + 1)
    den = np.bincount(idx, weights=(Nd * wgrid)[sel], minlength=len(g) + 1)

    gdp = _owid_csv('gdp-per-capita-worldbank')
    gdp = gdp[gdp['Year'] == 2000].set_index('Code')['GDP per capita'].to_dict()
    rows = []
    for i in range(1, len(g) + 1):
        iso = g.iloc[i - 1]['iso']
        if den[i] > 0 and iso in gdp:
            rows.append({'iso3': iso, 'gdp_pc_ppp': round(float(gdp[iso]), 1),
                         'hanpp_pct': round(num[i] / den[i] * 100, 3)})
    out = pd.DataFrame(rows).sort_values('gdp_pc_ppp')
    if len(out) < 30:
        raise RuntimeError("HANPP: unexpected row count")
    return _save(out, 'hanpp_real.csv')


_EUROSTAT_ISO3 = {
    'BE': 'BEL', 'BG': 'BGR', 'DE': 'DEU', 'EE': 'EST', 'EL': 'GRC',
    'ES': 'ESP', 'FR': 'FRA', 'IT': 'ITA', 'LV': 'LVA', 'LT': 'LTU',
    'LU': 'LUX', 'HU': 'HUN', 'NL': 'NLD', 'AT': 'AUT', 'PL': 'POL',
    'RO': 'ROU', 'SI': 'SVN', 'FI': 'FIN', 'NO': 'NOR', 'UK': 'GBR',
    'RS': 'SRB', 'TR': 'TUR',
}


def fetch_putnam():
    """#48 Putnam social capital PROXY: daily TV viewing vs generalized trust.

    This is a public-data PROXY reconstruction, not a replication of Putnam's
    original US-community measures. Matched on ISO3:
      - x = daily time watching television and video (hours): Eurostat
        Harmonised European Time Use Surveys (HETUS), dataset tus_00age,
        activity AC82 "Television and video", unit TIME_SP (mean time,
        total sex/age), most recent survey round per country (2000 or 2010).
      - y = generalized trust (% agreeing "most people can be trusted"): Our
        World in Data 'self-reported-trust-attitudes' (World Values Survey /
        integrated surveys), trust value from the year nearest the TV survey.
    Coverage is European (22 countries). Not a direct Putnam replication.
    """
    def _to_min(s):
        s = str(s)
        if ':' in s:
            h, m = s.split(':')
            return int(h) * 60 + int(m)
        return float(s)
    u = ('https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/'
         'tus_00age?format=JSON&sex=T&age=TOTAL&unit=TIME_SP&acl00=AC82')
    j = requests.get(u, timeout=TIMEOUT, headers=HEADERS).json()
    geo = j['dimension']['geo']['category']['index']
    tyr = j['dimension']['time']['category']['index']
    ids = j['id']
    nt = len(j['dimension'][ids[ids.index('time')]]['category']['index'])
    val = j['value']
    tv_rows = []
    for g, gp in geo.items():
        for t, tp in tyr.items():
            k = str(gp * nt + tp)
            if k in val:
                tv_rows.append({'geo': g, 'year': int(t),
                                'tv_min': _to_min(val[k])})
    tv = pd.DataFrame(tv_rows).sort_values('year').groupby('geo').tail(1)

    tr = _owid_csv('self-reported-trust-attitudes').dropna(
        subset=['Trust in others'])
    rows = []
    for _, r in tv.iterrows():
        iso = _EUROSTAT_ISO3.get(r['geo'])
        sub = tr[tr['Code'] == iso]
        if iso and len(sub):
            sub = sub.assign(d=(sub['Year'] - r['year']).abs()).sort_values('d')
            rr = sub.iloc[0]
            rows.append({'iso3': iso, 'tv_hours': round(r['tv_min'] / 60, 3),
                         'tv_year': int(r['year']),
                         'trust_pct': round(float(rr['Trust in others']), 2),
                         'trust_year': int(rr['Year'])})
    out = pd.DataFrame(rows).sort_values('tv_hours')
    if len(out) < 15:
        raise RuntimeError("Putnam: insufficient TV/trust overlap")
    return _save(out, 'putnam_real.csv')


FETCHERS = {
    'laffer': fetch_laffer,
    'great_gatsby': fetch_great_gatsby,
    'hanpp': fetch_hanpp,
    'putnam': fetch_putnam,
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
    'zipf': fetch_zipf,
    'lee_carter': fetch_lee_carter,
    'easterlin': fetch_easterlin,
    'engel': fetch_engel,
    'rahn': fetch_rahn,
    'hubble': fetch_hubble,
    'gravity': fetch_gravity,
    'species_area': fetch_species_area,
    'kleiber': fetch_kleiber,
    'duverger': fetch_duverger,
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
