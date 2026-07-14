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
        df['year'].values, np.log10(df['transistors_thousands'].values),
        x_label="Year", y_label="log\u2081\u2080(Transistors)",
        category="Physics",
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
