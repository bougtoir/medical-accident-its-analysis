"""
Build CurveReexamination objects from the additional real datasets fetched by
fetch_additional_real.py. These replace previously hard-coded arrays for:

  - Environmental Kuznets Curve (CO2) (#4) : World Bank WDI cross-section
  - Keeling Curve (CO2) (#31)              : NOAA GML Mauna Loa annual means
  - Gutenberg-Richter Law (#42)            : USGS FDSN earthquake catalog
  - Moore's Law (#43)                      : Karl Rupp transistor-count dataset
  - Balassa-Samuelson Effect (#12)         : Penn World Table 10.01

Variable transformations mirror the original analysis so verdicts are
comparable (e.g. log10 counts for Gutenberg-Richter and Moore).
"""

import os

import numpy as np
import pandas as pd

from core_analysis import CurveReexamination

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

# World Bank aggregate/regional codes (not independent country observations)
WB_AGGREGATE_CODES = {
    'WLD', 'UMC', 'TSS', 'SSA', 'SSF', 'TSA', 'SAS', 'SST', 'PRE', 'PST',
    'PSS', 'OSS', 'OED', 'INX', 'NAC', 'MIC', 'TMN', 'MNA', 'MEA', 'LMC',
    'LIC', 'LMY', 'LDC', 'TLA', 'LAC', 'LCN', 'LTE', 'IDA', 'IDX', 'IDB',
    'IBT', 'IBD', 'HIC', 'HPC', 'FCS', 'EUU', 'TEC', 'ECA', 'ECS', 'EMU',
    'TEA', 'EAP', 'EAS', 'EAR', 'CEB', 'CSS', 'ARB', 'AFW', 'AFE',
}


def _load(fname):
    path = os.path.join(DATA_DIR, fname)
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


def get_ekc_co2_real():
    df = _load('ekc_co2_real.csv')
    if df is None:
        return None
    if 'country_code' in df.columns:
        df = df[~df['country_code'].isin(WB_AGGREGATE_CODES)]
    df = df.dropna(subset=['gdp_pc_ppp', 'co2_pc'])
    df = df[(df['gdp_pc_ppp'] > 500) & (df['co2_pc'] > 0)]
    labels = df['country'].values if 'country' in df.columns else None
    return CurveReexamination(
        "Environmental Kuznets Curve (CO2)",
        df['gdp_pc_ppp'].values, df['co2_pc'].values,
        x_label="GDP per capita (PPP, $)", y_label="CO2 per capita (tonnes)",
        country_labels=labels, category="Economics",
    ), len(df)


def get_keeling_real():
    df = _load('keeling_real.csv')
    if df is None:
        return None
    df = df.dropna(subset=['year', 'co2_ppm'])
    return CurveReexamination(
        "Keeling Curve (CO2)", df['year'].values, df['co2_ppm'].values,
        x_label="Year", y_label="CO\u2082 Concentration (ppm)",
        category="Environmental Science",
    ), len(df)


def get_gutenberg_richter_real():
    df = _load('gutenberg_richter_real.csv')
    if df is None:
        return None
    df = df[df['annual_count'] > 0].dropna(subset=['magnitude', 'annual_count'])
    return CurveReexamination(
        "Gutenberg-Richter Law",
        df['magnitude'].values, np.log10(df['annual_count'].values),
        x_label="Magnitude", y_label="log\u2081\u2080(Annual Frequency)",
        category="Physics",
    ), len(df)


def get_moores_law_real():
    df = _load('moores_law_real.csv')
    if df is None:
        return None
    df = df.dropna(subset=['year', 'transistors_thousands'])
    df = df[df['transistors_thousands'] > 0]
    return CurveReexamination(
        "Moore's Law",
        df['year'].values, np.log10(df['transistors_thousands'].values * 1e3),
        x_label="Year", y_label="log\u2081\u2080(Transistors)",
        category="Physics",
    ), len(df)


def get_omran_real():
    df = _load('omran_real.csv')
    if df is None:
        return None
    df = df.dropna(subset=['hdi', 'ncd_share'])
    df = df[(df['hdi'] > 0) & (df['ncd_share'] > 0)]
    labels = df['country'].values if 'country' in df.columns else None
    return CurveReexamination(
        "Omran Epidemiological Transition",
        df['hdi'].values, df['ncd_share'].values,
        x_label="Human Development Index", y_label="NCD deaths (% of total)",
        country_labels=labels, category="Public Health",
    ), len(df)


def get_lipset_real():
    df = _load('lipset_real.csv')
    if df is None:
        return None
    df = df.dropna(subset=['gdp_pc_ppp', 'democracy'])
    df = df[df['gdp_pc_ppp'] > 0]
    labels = df['Country'].values if 'Country' in df.columns else None
    return CurveReexamination(
        "Lipset Hypothesis",
        df['gdp_pc_ppp'].values, df['democracy'].values,
        x_label="GDP per capita (PPP, $)",
        y_label="Democracy score (Freedom House, 0-1)",
        country_labels=labels, category="Political Science",
    ), len(df)


def get_beveridge_real():
    df = _load('beveridge_real.csv')
    if df is None:
        return None
    df = df.dropna(subset=['unemployment_rate', 'vacancy_rate'])
    df = df[(df['unemployment_rate'] > 0) & (df['vacancy_rate'] > 0)]
    return CurveReexamination(
        "Beveridge Curve",
        df['unemployment_rate'].values, df['vacancy_rate'].values,
        x_label="Unemployment Rate (%)", y_label="Vacancy Rate (%)",
        category="Economics",
    ), len(df)


def get_engel_real():
    df = _load('engel_real.csv')
    if df is None:
        return None
    df = df.dropna(subset=['gdp_pc_ppp', 'food_share'])
    df = df[(df['gdp_pc_ppp'] > 0) & (df['food_share'] > 0)]
    labels = df['country'].values if 'country' in df.columns else None
    return CurveReexamination(
        "Engel Curve",
        df['gdp_pc_ppp'].values, df['food_share'].values,
        x_label="GDP per capita (PPP, $)", y_label="Food Expenditure Share (%)",
        country_labels=labels, category="Economics",
    ), len(df)


def get_rahn_real():
    df = _load('rahn_real.csv')
    if df is None:
        return None
    df = df.dropna(subset=['gov_expenditure_gdp', 'gdp_growth'])
    df = df[df['gov_expenditure_gdp'] > 0]
    labels = df['country'].values if 'country' in df.columns else None
    return CurveReexamination(
        "Rahn Curve",
        df['gov_expenditure_gdp'].values, df['gdp_growth'].values,
        x_label="Government Spending (% of GDP)",
        y_label="Real GDP Growth (%, 2010-2019 avg)",
        country_labels=labels, category="Economics",
    ), len(df)


def get_easterlin_real():
    df = _load('easterlin_real.csv')
    if df is None:
        return None
    df = df.dropna(subset=['gdp_pc_ppp', 'happiness'])
    df = df[(df['gdp_pc_ppp'] > 0) & (df['happiness'] > 0)]
    labels = df['country'].values if 'country' in df.columns else None
    return CurveReexamination(
        "Easterlin Paradox",
        df['gdp_pc_ppp'].values, df['happiness'].values,
        x_label="GDP per capita (PPP, $)", y_label="Happiness Score (0-10)",
        country_labels=labels, category="Public Health",
    ), len(df)


def get_lee_carter_real():
    df = _load('lee_carter_real.csv')
    if df is None:
        return None
    df = df.dropna(subset=['year', 'kappa_t'])
    return CurveReexamination(
        "Lee-Carter Mortality Model",
        df['year'].values, df['kappa_t'].values,
        x_label="Year", y_label="Mortality Index (\u03ba_t)",
        category="Demography",
    ), len(df)


def get_zipf_real():
    df = _load('zipf_cities_real.csv')
    if df is None:
        return None
    df = df.dropna(subset=['rank', 'population'])
    df = df[df['population'] > 0]
    return CurveReexamination(
        "Zipf's Law (US Cities)",
        np.log(df['rank'].values), np.log(df['population'].values),
        x_label="log(Rank)", y_label="log(Population)",
        category="Political Science",
    ), len(df)


def get_hubbert_real():
    df = _load('hubbert_real.csv')
    if df is None:
        return None
    df = df.dropna(subset=['year', 'production_kbd'])
    df = df[df['production_kbd'] > 0]
    return CurveReexamination(
        "Hubbert Peak Oil (US)", df['year'].values, df['production_kbd'].values,
        x_label="Year", y_label="US crude oil production (thousand bbl/day)",
        category="Environmental Science",
    ), len(df)


def get_jevons_real():
    df = _load('jevons_real.csv')
    if df is None:
        return None
    df = df.dropna(subset=['intensity_btu_per_usd', 'total_energy_tbtu'])
    df = df[(df['intensity_btu_per_usd'] > 0) & (df['total_energy_tbtu'] > 0)]
    return CurveReexamination(
        "Jevons Paradox (Energy)",
        df['intensity_btu_per_usd'].values, df['total_energy_tbtu'].values,
        x_label="Energy intensity (Btu per real $ GDP)",
        y_label="Total primary energy consumption (Trillion Btu)",
        category="Environmental Science",
    ), len(df)


def get_balassa_samuelson_real():
    df = _load('balassa_samuelson_real.csv')
    if df is None:
        return None
    df = df.dropna(subset=['productivity_rel_us', 'price_level_rel_us'])
    df = df[(df['productivity_rel_us'] > 0) & (df['price_level_rel_us'] > 0)]
    labels = df['country'].values if 'country' in df.columns else None
    return CurveReexamination(
        "Balassa-Samuelson Effect",
        df['productivity_rel_us'].values, df['price_level_rel_us'].values,
        x_label="Relative Labor Productivity (US=100)",
        y_label="Relative Price Level (US=1.0)",
        country_labels=labels, category="Economics",
    ), len(df)


# curve_key -> (fetcher, exact result name it replaces, human source label)
ADDITIONAL_REAL = {
    'ekc_co2': (get_ekc_co2_real, 'Environmental Kuznets Curve (CO2)',
                'World Bank WDI (API)'),
    'keeling': (get_keeling_real, 'Keeling Curve (CO2)',
                'NOAA GML Mauna Loa'),
    'gutenberg_richter': (get_gutenberg_richter_real, 'Gutenberg-Richter Law',
                          'USGS FDSN earthquake catalog'),
    'moores_law': (get_moores_law_real, "Moore's Law",
                   'Karl Rupp microprocessor-trend-data'),
    'balassa_samuelson': (get_balassa_samuelson_real, 'Balassa-Samuelson Effect',
                          'Penn World Table 10.01'),
    'omran': (get_omran_real, 'Omran Epidemiological Transition',
              'UNDP HDI + World Bank WDI (NCD mortality)'),
    'lipset': (get_lipset_real, 'Lipset Hypothesis',
               'World Bank WDI + Freedom House (FIW)'),
    'hubbert': (get_hubbert_real, 'Hubbert Peak Oil (US)',
                'US EIA Total Energy (crude oil production)'),
    'jevons': (get_jevons_real, 'Jevons Paradox (Energy)',
               'US EIA Total Energy + World Bank WDI (US GDP)'),
    'beveridge': (get_beveridge_real, 'Beveridge Curve',
                  'US BLS (CPS unemployment + JOLTS job openings)'),
    'zipf': (get_zipf_real, "Zipf's Law (US Cities)",
             'US Census 2020 Decennial (place populations)'),
    'lee_carter': (get_lee_carter_real, 'Lee-Carter Mortality Model',
                   'HMD USA death rates (Lee-Carter SVD kappa_t)'),
    'easterlin': (get_easterlin_real, 'Easterlin Paradox',
                  'OWID Cantril ladder (WHR) + World Bank WDI GDP pc PPP'),
    'engel': (get_engel_real, 'Engel Curve',
              'OWID food expenditure share (USDA) + World Bank WDI GDP pc PPP'),
    'rahn': (get_rahn_real, 'Rahn Curve',
             'OWID govt expenditure (IMF) + World Bank WDI GDP growth'),
}


def get_all_additional_real():
    """Return dict of curve_name -> (CurveReexamination, N, source_label)."""
    out = {}
    for key, (fn, name, src) in ADDITIONAL_REAL.items():
        try:
            res = fn()
            if res is not None:
                crv, n = res
                out[name] = (crv, n, src)
                print(f"  Additional real data loaded: {name} (N={n}, {src})")
        except Exception as e:
            print(f"  Warning: {key} additional real data failed: {e}")
    return out


if __name__ == '__main__':
    d = get_all_additional_real()
    print(f"\nLoaded {len(d)} additional real curves")
    for name, (crv, n, src) in d.items():
        r = crv.run_full_analysis()
        print(f"{name}: N={n} verdict={r['verdict']['verdict']} "
              f"p_full={r['f_test']['p_value']:.4f} src={src}")
