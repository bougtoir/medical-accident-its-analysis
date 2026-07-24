"""Shared metadata and matrix helpers for archaic-segment analyses."""

from __future__ import annotations

import numpy as np
import pandas as pd


CHROM_SIZES = {
    "chr1": 248_956_422,
    "chr2": 242_193_529,
    "chr3": 198_295_559,
    "chr4": 190_214_555,
    "chr5": 181_538_259,
    "chr6": 170_805_979,
    "chr7": 159_345_973,
    "chr8": 145_138_636,
    "chr9": 138_394_717,
    "chr10": 133_797_422,
    "chr11": 135_086_622,
    "chr12": 133_275_309,
    "chr13": 114_364_328,
    "chr14": 107_043_718,
    "chr15": 101_991_189,
    "chr16": 90_338_345,
    "chr17": 83_257_441,
    "chr18": 80_373_285,
    "chr19": 58_617_616,
    "chr20": 64_444_167,
    "chr21": 46_709_983,
    "chr22": 50_818_468,
}

POP_COORDS = {
    "GBR": (51.5, -0.1),
    "FIN": (61.0, 25.0),
    "IBS": (40.0, -4.0),
    "CEU": (49.0, 8.0),
    "TSI": (43.5, 11.0),
    "CHB": (39.9, 116.4),
    "CHS": (23.1, 113.3),
    "CDX": (22.0, 100.0),
    "KHV": (16.0, 106.0),
    "JPT": (35.7, 139.7),
    "PUR": (18.2, -66.5),
    "CLM": (4.7, -74.1),
    "PEL": (-12.0, -77.0),
    "MXL": (23.6, -102.6),
    "PJL": (31.5, 73.0),
    "BEB": (23.7, 90.4),
    "STU": (7.9, 80.7),
    "ITU": (13.1, 80.3),
    "GIH": (23.0, 72.6),
    "French": (46.0, 2.0),
    "Sardinian": (40.0, 9.0),
    "Orcadian": (59.0, -3.0),
    "Russian": (55.0, 37.5),
    "BergamoItalian": (45.7, 9.7),
    "Tuscan": (43.3, 11.3),
    "Basque": (43.0, -2.0),
    "Adygei": (44.5, 40.0),
    "Druze": (32.5, 35.5),
    "Bedouin": (30.0, 35.0),
    "Palestinian": (31.9, 35.2),
    "Mozabite": (32.5, 3.7),
    "Brahui": (28.0, 66.0),
    "Balochi": (28.0, 66.5),
    "Hazara": (34.5, 67.0),
    "Makrani": (26.0, 63.0),
    "Sindhi": (25.4, 68.4),
    "Pathan": (34.0, 71.5),
    "Kalash": (35.7, 71.5),
    "Burusho": (36.3, 74.6),
    "Uygur": (41.0, 80.0),
    "Cambodian": (11.5, 105.0),
    "Japanese": (35.7, 139.7),
    "Han": (39.9, 116.4),
    "Yakut": (62.0, 130.0),
    "Tujia": (29.0, 109.0),
    "Yi": (27.0, 102.0),
    "Miao": (27.0, 109.0),
    "Oroqen": (50.5, 126.0),
    "Daur": (48.5, 124.0),
    "Mongolian": (47.0, 107.0),
    "Hezhen": (47.7, 132.0),
    "Xibo": (44.0, 81.0),
    "NorthernHan": (39.9, 116.4),
    "Dai": (21.0, 100.0),
    "Lahu": (22.5, 100.5),
    "She": (27.0, 119.0),
    "Naxi": (27.0, 100.0),
    "Tu": (36.5, 102.0),
    "Colombian": (2.0, -76.0),
    "Surui": (-11.0, -61.0),
    "Maya": (17.0, -89.0),
    "Karitiana": (-10.0, -63.0),
    "Pima": (28.0, -109.0),
    "Bougainville": (-6.2, 155.5),
    "PapuanSepik": (-4.0, 143.0),
    "PapuanHighlands": (-6.0, 145.0),
}

CONTINENT_MAP = {
    "CEU": "EUR",
    "FIN": "EUR",
    "GBR": "EUR",
    "IBS": "EUR",
    "TSI": "EUR",
    "French": "EUR",
    "Sardinian": "EUR",
    "Orcadian": "EUR",
    "Russian": "EUR",
    "BergamoItalian": "EUR",
    "Tuscan": "EUR",
    "Basque": "EUR",
    "Adygei": "EUR",
    "Druze": "WAS",
    "Bedouin": "WAS",
    "Palestinian": "WAS",
    "Mozabite": "WAS",
    "Brahui": "SAS",
    "Balochi": "SAS",
    "Hazara": "SAS",
    "Makrani": "SAS",
    "Sindhi": "SAS",
    "Pathan": "SAS",
    "Kalash": "SAS",
    "Burusho": "SAS",
    "Uygur": "SAS",
    "PJL": "SAS",
    "BEB": "SAS",
    "STU": "SAS",
    "ITU": "SAS",
    "GIH": "SAS",
    "CHB": "EAS",
    "CHS": "EAS",
    "CDX": "EAS",
    "KHV": "EAS",
    "JPT": "EAS",
    "Cambodian": "EAS",
    "Japanese": "EAS",
    "Han": "EAS",
    "Yakut": "EAS",
    "Tujia": "EAS",
    "Yi": "EAS",
    "Miao": "EAS",
    "Oroqen": "EAS",
    "Daur": "EAS",
    "Mongolian": "EAS",
    "Hezhen": "EAS",
    "Xibo": "EAS",
    "NorthernHan": "EAS",
    "Dai": "EAS",
    "Lahu": "EAS",
    "She": "EAS",
    "Naxi": "EAS",
    "Tu": "EAS",
    "PUR": "AMR",
    "CLM": "AMR",
    "PEL": "AMR",
    "MXL": "AMR",
    "Colombian": "AMR",
    "Surui": "AMR",
    "Maya": "AMR",
    "Karitiana": "AMR",
    "Pima": "AMR",
    "Bougainville": "OCE",
    "PapuanSepik": "OCE",
    "PapuanHighlands": "OCE",
}

ADMIXED_EUR_FRAC = {
    "PUR": 0.64,
    "CLM": 0.57,
    "MXL": 0.48,
    "PEL": 0.16,
}


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    phi1, phi2 = np.radians([lat1, lat2])
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)
    value = (
        np.sin(delta_phi / 2) ** 2
        + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2) ** 2
    )
    return float(2 * radius_km * np.arcsin(np.sqrt(value)))


def build_symmetric_matrix(
    pairs: pd.DataFrame, populations: list[str], value_column: str
) -> np.ndarray:
    index = {population: position for position, population in enumerate(populations)}
    matrix = np.full((len(populations), len(populations)), np.nan, dtype=float)
    np.fill_diagonal(matrix, 1.0 if "corr" in value_column else 0.0)
    for first_population, second_population, raw_value in pairs[
        ["pop1", "pop2", value_column]
    ].itertuples(index=False, name=None):
        first = index[first_population]
        second = index[second_population]
        value = float(raw_value)
        matrix[first, second] = value
        matrix[second, first] = value
    return matrix
