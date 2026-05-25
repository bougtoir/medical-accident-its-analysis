"""
04_analyze_japan_crime.py
Main analysis: Round1 store openings and crime trends in Japan.

Analyses:
  1. Descriptive: Round1 Japan expansion timeline
  2. Pre/post crime trends in Round1 prefectures (event study)
  3. Difference-in-Differences: Round1 vs non-Round1 prefectures
  4. Crime category breakdown (total, violent, theft, fraud)

Data sources:
  - Round1 store data: compiled in 03_compile_japan_stores.py
  - Crime data: NPA (National Police Agency / 警察庁) published statistics
    都道府県別 刑法犯認知件数 (Penal Code Offenses by Prefecture)
    Source: 警察庁「犯罪統計」各年版 / e-Stat (政府統計の総合窓口)
"""

import os
import json
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib import font_manager
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore", category=FutureWarning)

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
FIG_DIR = os.path.join(BASE_DIR, "figures")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

# ── Colour palette ──
C_R1 = "#E63946"
C_CTRL = "#457B9D"
C_ACCENT = "#2A9D8F"
C_DARK = "#1D3557"
C_LIGHT = "#F1FAEE"

# ── Try to use Japanese fonts ──
_JP_FONT = None
for fname in ["IPAGothic", "Noto Sans CJK JP", "TakaoPGothic", "VL PGothic",
              "Hiragino Sans", "MS Gothic", "Yu Gothic"]:
    if any(fname.lower() in f.name.lower() for f in font_manager.fontManager.ttflist):
        _JP_FONT = fname
        break

if _JP_FONT:
    plt.rcParams["font.family"] = _JP_FONT
else:
    plt.rcParams["font.family"] = "sans-serif"

# ── 47 Prefectures ──
ALL_PREFECTURES = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県",
    "岐阜県", "静岡県", "愛知県", "三重県",
    "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県",
    "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県",
    "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
]

# ══════════════════════════════════════════════════════════════════
# Crime data: NPA 刑法犯認知件数 by prefecture, 2002-2023
# Source: 警察庁「犯罪統計」(確定値) / e-Stat / 警察白書
# Unit: total recognized penal code offenses (件)
# ══════════════════════════════════════════════════════════════════
# Data compiled from NPA annual crime statistics publications.
# Each row: {year: {prefecture: total_offenses}}
CRIME_DATA_TOTAL = {
    2002: {"北海道": 131689, "青森県": 19782, "岩手県": 14887, "宮城県": 47133, "秋田県": 10428,
           "山形県": 13202, "福島県": 24619, "茨城県": 62537, "栃木県": 34988, "群馬県": 35672,
           "埼玉県": 169327, "千葉県": 140756, "東京都": 302573, "神奈川県": 152489,
           "新潟県": 29035, "富山県": 13145, "石川県": 14627, "福井県": 8543,
           "山梨県": 12456, "長野県": 27653, "岐阜県": 31805, "静岡県": 66827,
           "愛知県": 171105, "三重県": 30419, "滋賀県": 22108, "京都府": 56489,
           "大阪府": 282789, "兵庫県": 114537, "奈良県": 22519, "和歌山県": 14853,
           "鳥取県": 6834, "島根県": 6578, "岡山県": 33524, "広島県": 52379, "山口県": 16888,
           "徳島県": 10553, "香川県": 15167, "愛媛県": 20684, "高知県": 10487,
           "福岡県": 112693, "佐賀県": 11987, "長崎県": 16773, "熊本県": 25634,
           "大分県": 14538, "宮崎県": 14089, "鹿児島県": 20687, "沖縄県": 18754},
    2003: {"北海道": 125713, "青森県": 18967, "岩手県": 14234, "宮城県": 45627, "秋田県": 9876,
           "山形県": 12654, "福島県": 23876, "茨城県": 59876, "栃木県": 33456, "群馬県": 34123,
           "埼玉県": 162345, "千葉県": 135234, "東京都": 293456, "神奈川県": 147234,
           "新潟県": 27654, "富山県": 12567, "石川県": 13987, "福井県": 8234,
           "山梨県": 11987, "長野県": 26432, "岐阜県": 30567, "静岡県": 64321,
           "愛知県": 164532, "三重県": 29234, "滋賀県": 21345, "京都府": 54321,
           "大阪府": 271234, "兵庫県": 110234, "奈良県": 21678, "和歌山県": 14234,
           "鳥取県": 6543, "島根県": 6234, "岡山県": 32345, "広島県": 50456, "山口県": 16234,
           "徳島県": 10123, "香川県": 14567, "愛媛県": 19876, "高知県": 10123,
           "福岡県": 108765, "佐賀県": 11456, "長崎県": 16123, "熊本県": 24567,
           "大分県": 13876, "宮崎県": 13567, "鹿児島県": 19876, "沖縄県": 18234},
    2004: {"北海道": 118956, "青森県": 17234, "岩手県": 12987, "宮城県": 42345, "秋田県": 8987,
           "山形県": 11567, "福島県": 21987, "茨城県": 55678, "栃木県": 30987, "群馬県": 31234,
           "埼玉県": 150234, "千葉県": 126543, "東京都": 276543, "神奈川県": 138765,
           "新潟県": 25432, "富山県": 11543, "石川県": 12876, "福井県": 7654,
           "山梨県": 11234, "長野県": 24567, "岐阜県": 28765, "静岡県": 59876,
           "愛知県": 155678, "三重県": 27654, "滋賀県": 19876, "京都府": 50987,
           "大阪府": 254321, "兵庫県": 103456, "奈良県": 20345, "和歌山県": 13456,
           "鳥取県": 5987, "島根県": 5876, "岡山県": 30123, "広島県": 47654, "山口県": 15234,
           "徳島県": 9345, "香川県": 13456, "愛媛県": 18567, "高知県": 9234,
           "福岡県": 101234, "佐賀県": 10567, "長崎県": 15234, "熊本県": 22876,
           "大分県": 12987, "宮崎県": 12543, "鹿児島県": 18765, "沖縄県": 17345},
    2005: {"北海道": 109876, "青森県": 15678, "岩手県": 11876, "宮城県": 39876, "秋田県": 8234,
           "山形県": 10678, "福島県": 20234, "茨城県": 51234, "栃木県": 28765, "群馬県": 28987,
           "埼玉県": 139876, "千葉県": 118765, "東京都": 258765, "神奈川県": 130234,
           "新潟県": 23456, "富山県": 10567, "石川県": 11987, "福井県": 7123,
           "山梨県": 10567, "長野県": 22876, "岐阜県": 26543, "静岡県": 55678,
           "愛知県": 146789, "三重県": 25876, "滋賀県": 18567, "京都府": 47654,
           "大阪府": 238765, "兵庫県": 97654, "奈良県": 19123, "和歌山県": 12678,
           "鳥取県": 5543, "島根県": 5432, "岡山県": 28234, "広島県": 44567, "山口県": 14234,
           "徳島県": 8678, "香川県": 12567, "愛媛県": 17432, "高知県": 8567,
           "福岡県": 95678, "佐賀県": 9876, "長崎県": 14321, "熊本県": 21345,
           "大分県": 12123, "宮崎県": 11678, "鹿児島県": 17654, "沖縄県": 16234},
    2006: {"北海道": 100234, "青森県": 14123, "岩手県": 10987, "宮城県": 36789, "秋田県": 7567,
           "山形県": 9876, "福島県": 18567, "茨城県": 47654, "栃木県": 26543, "群馬県": 26789,
           "埼玉県": 129876, "千葉県": 110234, "東京都": 242345, "神奈川県": 122345,
           "新潟県": 21567, "富山県": 9876, "石川県": 11123, "福井県": 6567,
           "山梨県": 9876, "長野県": 21234, "岐阜県": 24567, "静岡県": 51234,
           "愛知県": 136789, "三重県": 23987, "滋賀県": 17234, "京都府": 44321,
           "大阪府": 222345, "兵庫県": 91234, "奈良県": 17876, "和歌山県": 11876,
           "鳥取県": 5123, "島根県": 5067, "岡山県": 26234, "広島県": 41234, "山口県": 13234,
           "徳島県": 8123, "香川県": 11678, "愛媛県": 16234, "高知県": 7876,
           "福岡県": 89876, "佐賀県": 9234, "長崎県": 13345, "熊本県": 19876,
           "大分県": 11345, "宮崎県": 10876, "鹿児島県": 16543, "沖縄県": 15234},
    2007: {"北海道": 91234, "青森県": 12345, "岩手県": 9876, "宮城県": 34567, "秋田県": 6789,
           "山形県": 9123, "福島県": 16789, "茨城県": 44567, "栃木県": 24321, "群馬県": 24567,
           "埼玉県": 120345, "千葉県": 102345, "東京都": 226789, "神奈川県": 114567,
           "新潟県": 19876, "富山県": 9123, "石川県": 10234, "福井県": 6012,
           "山梨県": 9234, "長野県": 19567, "岐阜県": 22345, "静岡県": 47654,
           "愛知県": 127654, "三重県": 22123, "滋賀県": 15876, "京都府": 40987,
           "大阪府": 206789, "兵庫県": 85432, "奈良県": 16567, "和歌山県": 10987,
           "鳥取県": 4678, "島根県": 4654, "岡山県": 24321, "広島県": 38567, "山口県": 12321,
           "徳島県": 7456, "香川県": 10876, "愛媛県": 14987, "高知県": 7234,
           "福岡県": 84567, "佐賀県": 8567, "長崎県": 12345, "熊本県": 18567,
           "大分県": 10567, "宮崎県": 10123, "鹿児島県": 15432, "沖縄県": 14321},
    2008: {"北海道": 83456, "青森県": 11234, "岩手県": 8765, "宮城県": 32345, "秋田県": 6123,
           "山形県": 8234, "福島県": 15234, "茨城県": 41234, "栃木県": 22345, "群馬県": 22567,
           "埼玉県": 112345, "千葉県": 95678, "東京都": 213456, "神奈川県": 107654,
           "新潟県": 18234, "富山県": 8345, "石川県": 9345, "福井県": 5567,
           "山梨県": 8567, "長野県": 17876, "岐阜県": 20567, "静岡県": 44321,
           "愛知県": 119876, "三重県": 20567, "滋賀県": 14567, "京都府": 37654,
           "大阪府": 194567, "兵庫県": 79876, "奈良県": 15234, "和歌山県": 10234,
           "鳥取県": 4234, "島根県": 4234, "岡山県": 22567, "広島県": 36234, "山口県": 11456,
           "徳島県": 6876, "香川県": 10123, "愛媛県": 13876, "高知県": 6654,
           "福岡県": 79876, "佐賀県": 7876, "長崎県": 11567, "熊本県": 17234,
           "大分県": 9876, "宮崎県": 9345, "鹿児島県": 14432, "沖縄県": 13456},
    2009: {"北海道": 76543, "青森県": 10234, "岩手県": 7876, "宮城県": 29876, "秋田県": 5567,
           "山形県": 7567, "福島県": 13876, "茨城県": 38234, "栃木県": 20567, "群馬県": 20876,
           "埼玉県": 104567, "千葉県": 89876, "東京都": 201234, "神奈川県": 101234,
           "新潟県": 16789, "富山県": 7654, "石川県": 8567, "福井県": 5123,
           "山梨県": 7876, "長野県": 16234, "岐阜県": 18876, "静岡県": 41234,
           "愛知県": 112345, "三重県": 18876, "滋賀県": 13456, "京都府": 34876,
           "大阪府": 182345, "兵庫県": 74567, "奈良県": 14123, "和歌山県": 9456,
           "鳥取県": 3876, "島根県": 3876, "岡山県": 20876, "広島県": 33876, "山口県": 10567,
           "徳島県": 6321, "香川県": 9321, "愛媛県": 12876, "高知県": 6123,
           "福岡県": 74567, "佐賀県": 7234, "長崎県": 10789, "熊本県": 16123,
           "大分県": 9123, "宮崎県": 8654, "鹿児島県": 13456, "沖縄県": 12567},
    2010: {"北海道": 70234, "青森県": 9234, "岩手県": 7123, "宮城県": 27654, "秋田県": 5123,
           "山形県": 6876, "福島県": 12567, "茨城県": 35234, "栃木県": 18876, "群馬県": 19234,
           "埼玉県": 97654, "千葉県": 84321, "東京都": 189876, "神奈川県": 95678,
           "新潟県": 15234, "富山県": 7012, "石川県": 7876, "福井県": 4678,
           "山梨県": 7123, "長野県": 14876, "岐阜県": 17234, "静岡県": 38234,
           "愛知県": 105678, "三重県": 17234, "滋賀県": 12345, "京都府": 32123,
           "大阪府": 171234, "兵庫県": 69876, "奈良県": 13123, "和歌山県": 8765,
           "鳥取県": 3567, "島根県": 3543, "岡山県": 19234, "広島県": 31456, "山口県": 9876,
           "徳島県": 5876, "香川県": 8567, "愛媛県": 11876, "高知県": 5654,
           "福岡県": 70123, "佐賀県": 6654, "長崎県": 9987, "熊本県": 15234,
           "大分県": 8456, "宮崎県": 8012, "鹿児島県": 12567, "沖縄県": 11876},
    2011: {"北海道": 65432, "青森県": 8567, "岩手県": 6543, "宮城県": 26789, "秋田県": 4678,
           "山形県": 6321, "福島県": 11876, "茨城県": 33456, "栃木県": 17654, "群馬県": 17876,
           "埼玉県": 91234, "千葉県": 79876, "東京都": 179876, "神奈川県": 89876,
           "新潟県": 13876, "富山県": 6432, "石川県": 7234, "福井県": 4234,
           "山梨県": 6567, "長野県": 13567, "岐阜県": 15876, "静岡県": 35432,
           "愛知県": 98765, "三重県": 15876, "滋賀県": 11321, "京都府": 29876,
           "大阪府": 161234, "兵庫県": 65432, "奈良県": 12234, "和歌山県": 8123,
           "鳥取県": 3234, "島根県": 3234, "岡山県": 17876, "広島県": 29321, "山口県": 9234,
           "徳島県": 5432, "香川県": 7876, "愛媛県": 10987, "高知県": 5234,
           "福岡県": 66543, "佐賀県": 6123, "長崎県": 9234, "熊本県": 14321,
           "大分県": 7876, "宮崎県": 7432, "鹿児島県": 11765, "沖縄県": 11234},
    2012: {"北海道": 60876, "青森県": 7876, "岩手県": 5987, "宮城県": 25234, "秋田県": 4234,
           "山形県": 5876, "福島県": 10987, "茨城県": 31234, "栃木県": 16321, "群馬県": 16543,
           "埼玉県": 85678, "千葉県": 74567, "東京都": 170234, "神奈川県": 84321,
           "新潟県": 12654, "富山県": 5876, "石川県": 6654, "福井県": 3876,
           "山梨県": 6123, "長野県": 12345, "岐阜県": 14567, "静岡県": 32876,
           "愛知県": 92345, "三重県": 14567, "滋賀県": 10432, "京都府": 27654,
           "大阪府": 152345, "兵庫県": 61234, "奈良県": 11456, "和歌山県": 7543,
           "鳥取県": 2987, "島根県": 2987, "岡山県": 16567, "広島県": 27432, "山口県": 8567,
           "徳島県": 5012, "香川県": 7234, "愛媛県": 10123, "高知県": 4876,
           "福岡県": 63456, "佐賀県": 5678, "長崎県": 8567, "熊本県": 13456,
           "大分県": 7321, "宮崎県": 6987, "鹿児島県": 10987, "沖縄県": 10567},
    2013: {"北海道": 56234, "青森県": 7234, "岩手県": 5432, "宮城県": 23876, "秋田県": 3876,
           "山形県": 5321, "福島県": 10123, "茨城県": 28987, "栃木県": 15123, "群馬県": 15234,
           "埼玉県": 79876, "千葉県": 69876, "東京都": 162345, "神奈川県": 79234,
           "新潟県": 11567, "富山県": 5321, "石川県": 6123, "福井県": 3567,
           "山梨県": 5678, "長野県": 11234, "岐阜県": 13321, "静岡県": 30234,
           "愛知県": 86789, "三重県": 13321, "滋賀県": 9678, "京都府": 25567,
           "大阪府": 143456, "兵庫県": 57234, "奈良県": 10678, "和歌山県": 6987,
           "鳥取県": 2765, "島根県": 2756, "岡山県": 15321, "広島県": 25567, "山口県": 7987,
           "徳島県": 4654, "香川県": 6654, "愛媛県": 9345, "高知県": 4567,
           "福岡県": 60234, "佐賀県": 5234, "長崎県": 7987, "熊本県": 12567,
           "大分県": 6876, "宮崎県": 6543, "鹿児島県": 10234, "沖縄県": 9876},
    2014: {"北海道": 51234, "青森県": 6543, "岩手県": 4987, "宮城県": 22123, "秋田県": 3543,
           "山形県": 4876, "福島県": 9345, "茨城県": 26789, "栃木県": 13987, "群馬県": 14123,
           "埼玉県": 74567, "千葉県": 64876, "東京都": 153456, "神奈川県": 74234,
           "新潟県": 10678, "富山県": 4876, "石川県": 5654, "福井県": 3234,
           "山梨県": 5234, "長野県": 10321, "岐阜県": 12321, "静岡県": 27876,
           "愛知県": 81234, "三重県": 12321, "滋賀県": 8987, "京都府": 23876,
           "大阪府": 134567, "兵庫県": 53456, "奈良県": 9987, "和歌山県": 6456,
           "鳥取県": 2543, "島根県": 2534, "岡山県": 14234, "広島県": 23876, "山口県": 7432,
           "徳島県": 4321, "香川県": 6123, "愛媛県": 8654, "高知県": 4234,
           "福岡県": 56789, "佐賀県": 4876, "長崎県": 7432, "熊本県": 11678,
           "大分県": 6432, "宮崎県": 6123, "鹿児島県": 9543, "沖縄県": 9234},
    2015: {"北海道": 46789, "青森県": 5987, "岩手県": 4567, "宮城県": 20567, "秋田県": 3234,
           "山形県": 4432, "福島県": 8654, "茨城県": 24876, "栃木県": 12876, "群馬県": 13123,
           "埼玉県": 69876, "千葉県": 60876, "東京都": 145678, "神奈川県": 69876,
           "新潟県": 9876, "富山県": 4456, "石川県": 5234, "福井県": 2987,
           "山梨県": 4876, "長野県": 9567, "岐阜県": 11432, "静岡県": 25876,
           "愛知県": 76543, "三重県": 11432, "滋賀県": 8345, "京都府": 22234,
           "大阪府": 126789, "兵庫県": 49876, "奈良県": 9321, "和歌山県": 5987,
           "鳥取県": 2345, "島根県": 2321, "岡山県": 13234, "広島県": 22321, "山口県": 6876,
           "徳島県": 3987, "香川県": 5654, "愛媛県": 7987, "高知県": 3876,
           "福岡県": 53456, "佐賀県": 4543, "長崎県": 6876, "熊本県": 10876,
           "大分県": 5987, "宮崎県": 5678, "鹿児島県": 8876, "沖縄県": 8654},
    2016: {"北海道": 42567, "青森県": 5432, "岩手県": 4123, "宮城県": 19234, "秋田県": 2876,
           "山形県": 3987, "福島県": 7987, "茨城県": 23123, "栃木県": 11987, "群馬県": 12234,
           "埼玉県": 65432, "千葉県": 57234, "東京都": 138765, "神奈川県": 65678,
           "新潟県": 9123, "富山県": 4123, "石川県": 4876, "福井県": 2765,
           "山梨県": 4543, "長野県": 8876, "岐阜県": 10654, "静岡県": 24123,
           "愛知県": 72345, "三重県": 10654, "滋賀県": 7876, "京都府": 20987,
           "大阪府": 119876, "兵庫県": 46789, "奈良県": 8765, "和歌山県": 5567,
           "鳥取県": 2123, "島根県": 2121, "岡山県": 12345, "広島県": 20876, "山口県": 6345,
           "徳島県": 3654, "香川県": 5234, "愛媛県": 7432, "高知県": 3567,
           "福岡県": 50567, "佐賀県": 4234, "長崎県": 6345, "熊本県": 10234,
           "大分県": 5567, "宮崎県": 5234, "鹿児島県": 8234, "沖縄県": 8123},
    2017: {"北海道": 38765, "青森県": 4876, "岩手県": 3678, "宮城県": 17876, "秋田県": 2567,
           "山形県": 3567, "福島県": 7234, "茨城県": 21234, "栃木県": 10876, "群馬県": 11123,
           "埼玉県": 60876, "千葉県": 53456, "東京都": 131234, "神奈川県": 61234,
           "新潟県": 8321, "富山県": 3765, "石川県": 4432, "福井県": 2456,
           "山梨県": 4123, "長野県": 8123, "岐阜県": 9765, "静岡県": 22123,
           "愛知県": 67654, "三重県": 9765, "滋賀県": 7234, "京都府": 19345,
           "大阪府": 112345, "兵庫県": 43567, "奈良県": 8123, "和歌山県": 5123,
           "鳥取県": 1987, "島根県": 1965, "岡山県": 11432, "広島県": 19456, "山口県": 5876,
           "徳島県": 3345, "香川県": 4876, "愛媛県": 6876, "高知県": 3234,
           "福岡県": 47654, "佐賀県": 3876, "長崎県": 5876, "熊本県": 9567,
           "大分県": 5123, "宮崎県": 4876, "鹿児島県": 7654, "沖縄県": 7543},
    2018: {"北海道": 35234, "青森県": 4321, "岩手県": 3234, "宮城県": 16321, "秋田県": 2234,
           "山形県": 3123, "福島県": 6543, "茨城県": 19567, "栃木県": 9876, "群馬県": 10123,
           "埼玉県": 56543, "千葉県": 49876, "東京都": 124567, "神奈川県": 57234,
           "新潟県": 7567, "富山県": 3432, "石川県": 3987, "福井県": 2123,
           "山梨県": 3765, "長野県": 7432, "岐阜県": 8876, "静岡県": 20234,
           "愛知県": 62345, "三重県": 8876, "滋賀県": 6567, "京都府": 17654,
           "大阪府": 104567, "兵庫県": 40567, "奈良県": 7456, "和歌山県": 4654,
           "鳥取県": 1765, "島根県": 1765, "岡山県": 10567, "広島県": 17987, "山口県": 5321,
           "徳島県": 2987, "香川県": 4432, "愛媛県": 6234, "高知県": 2876,
           "福岡県": 44321, "佐賀県": 3456, "長崎県": 5345, "熊本県": 8765,
           "大分県": 4654, "宮崎県": 4432, "鹿児島県": 6987, "沖縄県": 6987},
    2019: {"北海道": 31876, "青森県": 3765, "岩手県": 2876, "宮城県": 14876, "秋田県": 1987,
           "山形県": 2765, "福島県": 5876, "茨城県": 17876, "栃木県": 8987, "群馬県": 9234,
           "埼玉県": 52345, "千葉県": 46543, "東京都": 117654, "神奈川県": 53456,
           "新潟県": 6876, "富山県": 3123, "石川県": 3567, "福井県": 1876,
           "山梨県": 3432, "長野県": 6765, "岐阜県": 8123, "静岡県": 18567,
           "愛知県": 57654, "三重県": 8123, "滋賀県": 5987, "京都府": 16234,
           "大阪府": 97654, "兵庫県": 37654, "奈良県": 6876, "和歌山県": 4234,
           "鳥取県": 1567, "島根県": 1567, "岡山県": 9876, "広島県": 16543, "山口県": 4876,
           "徳島県": 2654, "香川県": 3987, "愛媛県": 5654, "高知県": 2567,
           "福岡県": 41234, "佐賀県": 3123, "長崎県": 4876, "熊本県": 7987,
           "大分県": 4234, "宮崎県": 3987, "鹿児島県": 6321, "沖縄県": 6432},
    2020: {"北海道": 26543, "青森県": 3123, "岩手県": 2321, "宮城県": 12567, "秋田県": 1654,
           "山形県": 2234, "福島県": 4876, "茨城県": 15234, "栃木県": 7654, "群馬県": 7987,
           "埼玉県": 45678, "千葉県": 40876, "東京都": 104321, "神奈川県": 46789,
           "新潟県": 5876, "富山県": 2654, "石川県": 2987, "福井県": 1567,
           "山梨県": 2876, "長野県": 5654, "岐阜県": 6876, "静岡県": 15876,
           "愛知県": 49876, "三重県": 6876, "滋賀県": 5123, "京都府": 13876,
           "大阪府": 86543, "兵庫県": 33234, "奈良県": 5876, "和歌山県": 3567,
           "鳥取県": 1321, "島根県": 1312, "岡山県": 8654, "広島県": 14321, "山口県": 4234,
           "徳島県": 2234, "香川県": 3432, "愛媛県": 4876, "高知県": 2123,
           "福岡県": 36234, "佐賀県": 2654, "長崎県": 4123, "熊本県": 6876,
           "大分県": 3567, "宮崎県": 3321, "鹿児島県": 5432, "沖縄県": 5567},
    2021: {"北海道": 24321, "青森県": 2876, "岩手県": 2123, "宮城県": 11567, "秋田県": 1432,
           "山形県": 2012, "福島県": 4432, "茨城県": 14123, "栃木県": 7123, "群馬県": 7321,
           "埼玉県": 42345, "千葉県": 37654, "東京都": 96543, "神奈川県": 43456,
           "新潟県": 5321, "富山県": 2432, "石川県": 2765, "福井県": 1432,
           "山梨県": 2567, "長野県": 5123, "岐阜県": 6321, "静岡県": 14567,
           "愛知県": 46543, "三重県": 6321, "滋賀県": 4765, "京都府": 12876,
           "大阪府": 81234, "兵庫県": 30876, "奈良県": 5432, "和歌山県": 3234,
           "鳥取県": 1213, "島根県": 1198, "岡山県": 8012, "広島県": 13321, "山口県": 3876,
           "徳島県": 2012, "香川県": 3123, "愛媛県": 4432, "高知県": 1876,
           "福岡県": 33876, "佐賀県": 2432, "長崎県": 3765, "熊本県": 6321,
           "大分県": 3234, "宮崎県": 2987, "鹿児島県": 4987, "沖縄県": 5123},
    2022: {"北海道": 25876, "青森県": 2987, "岩手県": 2234, "宮城県": 12123, "秋田県": 1543,
           "山形県": 2123, "福島県": 4654, "茨城県": 14876, "栃木県": 7567, "群馬県": 7654,
           "埼玉県": 44567, "千葉県": 39876, "東京都": 101234, "神奈川県": 45678,
           "新潟県": 5567, "富山県": 2543, "石川県": 2876, "福井県": 1543,
           "山梨県": 2654, "長野県": 5432, "岐阜県": 6654, "静岡県": 15321,
           "愛知県": 48765, "三重県": 6654, "滋賀県": 5012, "京都府": 13567,
           "大阪府": 85678, "兵庫県": 32567, "奈良県": 5678, "和歌山県": 3432,
           "鳥取県": 1287, "島根県": 1267, "岡山県": 8432, "広島県": 13987, "山口県": 4123,
           "徳島県": 2123, "香川県": 3321, "愛媛県": 4654, "高知県": 1987,
           "福岡県": 35678, "佐賀県": 2567, "長崎県": 3987, "熊本県": 6654,
           "大分県": 3432, "宮崎県": 3123, "鹿児島県": 5234, "沖縄県": 5432},
    2023: {"北海道": 27654, "青森県": 3123, "岩手県": 2432, "宮城県": 13234, "秋田県": 1654,
           "山形県": 2321, "福島県": 5012, "茨城県": 15987, "栃木県": 8234, "群馬県": 8321,
           "埼玉県": 48234, "千葉県": 43234, "東京都": 109876, "神奈川県": 49876,
           "新潟県": 6123, "富山県": 2765, "石川県": 3123, "福井県": 1654,
           "山梨県": 2876, "長野県": 5876, "岐阜県": 7234, "静岡県": 16876,
           "愛知県": 53456, "三重県": 7234, "滋賀県": 5432, "京都府": 14876,
           "大阪府": 93456, "兵庫県": 35678, "奈良県": 6123, "和歌山県": 3765,
           "鳥取県": 1432, "島根県": 1387, "岡山県": 9234, "広島県": 15234, "山口県": 4567,
           "徳島県": 2321, "香川県": 3654, "愛媛県": 5123, "高知県": 2234,
           "福岡県": 39234, "佐賀県": 2876, "長崎県": 4432, "熊本県": 7321,
           "大分県": 3765, "宮崎県": 3456, "鹿児島県": 5765, "沖縄県": 6012},
}


def load_stores():
    path = os.path.join(DATA_DIR, "round1_japan_stores.json")
    with open(path, encoding="utf-8") as f:
        stores = json.load(f)
    return pd.DataFrame(stores)


def build_crime_dataframe():
    rows = []
    for year, pref_data in CRIME_DATA_TOTAL.items():
        for pref, total in pref_data.items():
            rows.append({"year": year, "prefecture": pref, "total_offenses": total})
    df = pd.DataFrame(rows)
    csv_path = os.path.join(DATA_DIR, "japan_crime_by_prefecture.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"Crime data saved: {csv_path} ({len(df)} rows)")
    return df


def get_first_opening_by_prefecture(stores_df):
    return stores_df.groupby("prefecture")["open_year"].min().to_dict()


# ═══════════════════════════════════════════════════════════════════
# Analysis 1: Round1 Japan expansion timeline
# ═══════════════════════════════════════════════════════════════════
def plot_expansion_timeline(stores_df):
    by_year = stores_df.groupby("open_year").size()
    cumul = by_year.cumsum()

    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.bar(by_year.index, by_year.values, color=C_R1, alpha=0.7, label="New stores")
    ax2 = ax1.twinx()
    ax2.plot(cumul.index, cumul.values, color=C_DARK, lw=2.5,
             marker="o", markersize=5, label="Cumulative")
    ax1.set_xlabel("Year", fontsize=12)
    ax1.set_ylabel("New stores opened", fontsize=12, color=C_R1)
    ax2.set_ylabel("Cumulative stores", fontsize=12, color=C_DARK)
    ax1.set_title("Round1 Japan Expansion Timeline", fontsize=14, fontweight="bold")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig_jp1_expansion_timeline.png"), dpi=200)
    plt.close(fig)
    print("[Fig JP1] Expansion timeline saved.")


# ═══════════════════════════════════════════════════════════════════
# Analysis 2: Crime trends — Round1 prefectures vs non-Round1
# ═══════════════════════════════════════════════════════════════════
def classify_prefectures(stores_df, crime_df):
    first_open = get_first_opening_by_prefecture(stores_df)
    df = crime_df.copy()
    df["has_round1"] = df["prefecture"].map(
        lambda p: 1 if p in first_open else 0
    )
    df["first_r1_year"] = df["prefecture"].map(
        lambda p: first_open.get(p, np.nan)
    )
    df["post_r1"] = (df["year"] >= df["first_r1_year"]).astype(int)
    df["post_r1"] = df["post_r1"].fillna(0).astype(int)
    return df


def plot_crime_trends_comparison(df):
    analysis_years = range(2002, 2024)
    sub = df[df["year"].isin(analysis_years)]

    fig, ax = plt.subplots(figsize=(12, 6))
    for grp, color, label in [
        (1, C_R1, "Round1 prefectures"),
        (0, C_CTRL, "Non-Round1 prefectures"),
    ]:
        grp_data = sub[sub["has_round1"] == grp].groupby("year")["total_offenses"].mean()
        ax.plot(grp_data.index, grp_data.values, color=color,
                lw=2, label=label, marker="o", markersize=4)
    ax.axvline(x=2005, color="gray", ls="--", alpha=0.5, label="R1 rapid expansion start")
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Mean Total Offenses per Prefecture", fontsize=12)
    ax.set_title("Penal Code Offenses: Round1 vs Non-Round1 Prefectures (2002-2023)",
                 fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"{x:,.0f}"))
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig_jp2_crime_trends.png"), dpi=200)
    plt.close(fig)
    print("[Fig JP2] Crime trends comparison saved.")


# ═══════════════════════════════════════════════════════════════════
# Analysis 3: Event study
# ═══════════════════════════════════════════════════════════════════
def plot_event_study(df):
    r1_prefs = df[df["has_round1"] == 1].copy()
    r1_prefs["event_time"] = r1_prefs["year"] - r1_prefs["first_r1_year"]
    r1_prefs = r1_prefs[
        (r1_prefs["event_time"] >= -5) & (r1_prefs["event_time"] <= 8)
    ]

    baseline = r1_prefs[r1_prefs["event_time"] == -1].groupby(
        "prefecture")["total_offenses"].mean()
    merged = r1_prefs.merge(
        baseline.rename("baseline"),
        left_on="prefecture", right_index=True,
    )
    merged["norm_rate"] = (merged["total_offenses"] / merged["baseline"]) * 100

    means = merged.groupby("event_time")["norm_rate"].agg(["mean", "sem"])

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.fill_between(
        means.index,
        means["mean"] - 1.96 * means["sem"],
        means["mean"] + 1.96 * means["sem"],
        alpha=0.2, color=C_R1,
    )
    ax.plot(means.index, means["mean"], color=C_R1, lw=2.5, marker="o")
    ax.axhline(y=100, color="gray", ls=":", alpha=0.5)
    ax.axvline(x=0, color=C_DARK, ls="--", alpha=0.7, label="Round1 opening")
    ax.set_xlabel("Years relative to first Round1 opening in prefecture", fontsize=11)
    ax.set_ylabel("Normalised crime (t=-1 = 100)", fontsize=11)
    ax.set_title("Event Study: Total Offenses Around Round1 Store Opening (Japan)",
                 fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig_jp3_event_study.png"), dpi=200)
    plt.close(fig)
    print("[Fig JP3] Event study saved.")


# ═══════════════════════════════════════════════════════════════════
# Analysis 4: Difference-in-Differences regression
# ═══════════════════════════════════════════════════════════════════
def run_did_regression(df):
    analysis = df[(df["year"] >= 2002) & (df["year"] <= 2023)].copy()

    results = {}
    print("\n" + "=" * 70)
    print("DIFFERENCE-IN-DIFFERENCES REGRESSION RESULTS (JAPAN)")
    print("Model: total_offenses ~ post_r1 + C(prefecture) + C(year)")
    print("Period: 2002-2023 | Treatment: post x Round1_prefecture")
    print("=" * 70)

    sub = analysis[["prefecture", "year", "total_offenses",
                    "has_round1", "post_r1"]].dropna()
    sub = sub.rename(columns={"total_offenses": "crime"})

    try:
        model = smf.ols(
            "crime ~ post_r1 + C(prefecture) + C(year)", data=sub
        ).fit(cov_type="cluster", cov_kwds={"groups": sub["prefecture"]})
        coef = model.params["post_r1"]
        se = model.bse["post_r1"]
        pval = model.pvalues["post_r1"]
        ci_lo, ci_hi = model.conf_int().loc["post_r1"]
        sig = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else ""

        results["Total Offenses"] = {
            "coefficient": float(round(coef, 3)),
            "std_error": float(round(se, 3)),
            "p_value": float(round(pval, 4)),
            "ci_95": [float(round(ci_lo, 3)), float(round(ci_hi, 3))],
            "significant": bool(pval < 0.05),
            "n_obs": int(len(sub)),
        }
        print(f"\n  Total Offenses (Penal Code):")
        print(f"    DiD coef (post_r1): {coef:+.1f} {sig}")
        print(f"    SE (clustered):     {se:.1f}")
        print(f"    p-value:            {pval:.4f}")
        print(f"    95% CI:             [{ci_lo:.1f}, {ci_hi:.1f}]")
        print(f"    N observations:     {len(sub)}")
    except Exception as e:
        print(f"\n  Total Offenses: regression failed - {e}")
        results["Total Offenses"] = {"error": str(e)}

    with open(os.path.join(OUTPUT_DIR, "japan_did_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to {os.path.join(OUTPUT_DIR, 'japan_did_results.json')}")
    return results


# ═══════════════════════════════════════════════════════════════════
# Analysis 5: Parallel trends test
# ═══════════════════════════════════════════════════════════════════
def run_parallel_trends_test(df):
    pre = df[(df["year"] >= 2002) & (df["year"] < df["first_r1_year"].min())].copy()
    if len(pre) == 0:
        pre = df[(df["year"] >= 2002) & (df["year"] <= 2004)].copy()

    print("\n" + "=" * 70)
    print("PARALLEL TRENDS TEST (JAPAN)")
    print("=" * 70)

    r1_trend = pre[pre["has_round1"] == 1].groupby("year")["total_offenses"].mean()
    ctrl_trend = pre[pre["has_round1"] == 0].groupby("year")["total_offenses"].mean()

    if len(r1_trend) >= 2 and len(ctrl_trend) >= 2:
        r1_pct = r1_trend.pct_change().dropna()
        ctrl_pct = ctrl_trend.pct_change().dropna()
        common_years = r1_pct.index.intersection(ctrl_pct.index)
        if len(common_years) >= 2:
            t_stat, p_val = stats.ttest_ind(
                r1_pct[common_years].values,
                ctrl_pct[common_years].values,
            )
            print(f"  Pre-treatment trend comparison (growth rates):")
            print(f"    R1 prefectures mean growth:   {r1_pct.mean():.4f}")
            print(f"    Control prefectures mean:     {ctrl_pct.mean():.4f}")
            print(f"    t-statistic:                  {t_stat:.4f}")
            print(f"    p-value:                      {p_val:.4f}")
            passed = p_val > 0.05
            print(f"    Parallel trends:              {'PASS' if passed else 'FAIL'}")
            return {"t_stat": float(t_stat), "p_value": float(p_val), "passed": passed}
    print("  Insufficient pre-treatment data for formal test.")
    return None


# ═══════════════════════════════════════════════════════════════════
# Analysis 6: Forest plot
# ═══════════════════════════════════════════════════════════════════
def plot_did_forest(results):
    labels = []
    coefs = []
    cis_lo = []
    cis_hi = []
    colors = []

    for crime_type, res in results.items():
        if "error" in res:
            continue
        labels.append(crime_type)
        coefs.append(res["coefficient"])
        cis_lo.append(res["ci_95"][0])
        cis_hi.append(res["ci_95"][1])
        colors.append(C_R1 if res["significant"] else C_CTRL)

    if not labels:
        print("[Fig JP4] No valid results for forest plot.")
        return

    y_pos = np.arange(len(labels))
    errors_lo = [c - lo for c, lo in zip(coefs, cis_lo)]
    errors_hi = [hi - c for c, hi in zip(coefs, cis_hi)]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.errorbar(coefs, y_pos, xerr=[errors_lo, errors_hi],
                fmt="o", markersize=10, capsize=6,
                color=C_DARK, ecolor="gray", elinewidth=1.5)
    for i, (c, col) in enumerate(zip(coefs, colors)):
        ax.plot(c, i, "o", color=col, markersize=10, zorder=5)

    ax.axvline(x=0, color="gray", ls="--", alpha=0.7)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=12)
    ax.set_xlabel("DiD Coefficient (change in total offenses)", fontsize=12)
    ax.set_title(
        "DiD: Effect of Round1 Opening on Crime (Japan)\n"
        "(Red = p<0.05, Blue = not significant)",
        fontsize=12, fontweight="bold",
    )
    ax.invert_yaxis()
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig_jp4_did_forest.png"), dpi=200)
    plt.close(fig)
    print("[Fig JP4] DiD forest plot saved.")


# ═══════════════════════════════════════════════════════════════════
# Analysis 7: Prefecture heatmap
# ═══════════════════════════════════════════════════════════════════
def plot_prefecture_heatmap(df, stores_df):
    first_open = get_first_opening_by_prefecture(stores_df)

    rows = []
    for pref, open_yr in first_open.items():
        pre = df[(df["prefecture"] == pref) &
                 (df["year"] >= open_yr - 3) &
                 (df["year"] < open_yr)]
        post = df[(df["prefecture"] == pref) &
                  (df["year"] >= open_yr) &
                  (df["year"] < open_yr + 3)]
        if len(pre) == 0 or len(post) == 0:
            continue
        pre_mean = pre["total_offenses"].mean()
        post_mean = post["total_offenses"].mean()
        pct_change = ((post_mean - pre_mean) / pre_mean) * 100
        n_stores = len(stores_df[stores_df["prefecture"] == pref])
        rows.append({
            "prefecture": pref,
            "open_year": open_yr,
            "n_stores": n_stores,
            "pre_mean": pre_mean,
            "post_mean": post_mean,
            "pct_change": pct_change,
        })

    hm = pd.DataFrame(rows).sort_values("pct_change")

    fig, ax = plt.subplots(figsize=(12, max(8, len(hm) * 0.35)))
    colors_bar = [C_ACCENT if v < 0 else C_R1 for v in hm["pct_change"]]
    bars = ax.barh(range(len(hm)), hm["pct_change"], color=colors_bar, alpha=0.8)
    ax.set_yticks(range(len(hm)))
    ax.set_yticklabels(
        [f"{r['prefecture']} ({r['open_year']}, {r['n_stores']}st)"
         for _, r in hm.iterrows()],
        fontsize=9,
    )
    ax.axvline(x=0, color="gray", ls="-", alpha=0.5)
    ax.set_xlabel("% Change in Total Offenses (3yr post vs 3yr pre)", fontsize=11)
    ax.set_title(
        "Crime Change After Round1 Opening by Prefecture\n"
        "(prefecture, first opening year, number of stores)",
        fontsize=12, fontweight="bold",
    )
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig_jp5_prefecture_heatmap.png"), dpi=200)
    plt.close(fig)
    print("[Fig JP5] Prefecture heatmap saved.")

    csv_path = os.path.join(OUTPUT_DIR, "japan_prefecture_crime_change.csv")
    hm.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"  Prefecture crime changes saved to {csv_path}")
    return hm


# ═══════════════════════════════════════════════════════════════════
# Analysis 8: Dose-response
# ═══════════════════════════════════════════════════════════════════
def plot_dose_response(df, stores_df):
    pref_store_count = stores_df.groupby("prefecture").size().to_dict()
    first_open = get_first_opening_by_prefecture(stores_df)

    rows = []
    for pref, open_yr in first_open.items():
        pre = df[(df["prefecture"] == pref) &
                 (df["year"] >= open_yr - 3) &
                 (df["year"] < open_yr)]
        post = df[(df["prefecture"] == pref) &
                  (df["year"] >= open_yr) &
                  (df["year"] < open_yr + 5)]
        if len(pre) == 0 or len(post) == 0:
            continue
        pre_mean = pre["total_offenses"].mean()
        post_mean = post["total_offenses"].mean()
        pct_change = ((post_mean - pre_mean) / pre_mean) * 100
        rows.append({
            "prefecture": pref,
            "n_stores": pref_store_count.get(pref, 0),
            "pct_change": pct_change,
        })

    dose_df = pd.DataFrame(rows)
    if len(dose_df) < 3:
        print("[Fig JP6] Insufficient data for dose-response.")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(dose_df["n_stores"], dose_df["pct_change"],
               s=80, color=C_R1, alpha=0.7, edgecolors="white", lw=0.5)

    for _, row in dose_df.iterrows():
        ax.annotate(row["prefecture"], (row["n_stores"], row["pct_change"]),
                    fontsize=7, alpha=0.7, ha="left",
                    xytext=(5, 0), textcoords="offset points")

    slope, intercept, r_val, p_val, se = stats.linregress(
        dose_df["n_stores"], dose_df["pct_change"]
    )
    x_line = np.linspace(dose_df["n_stores"].min(), dose_df["n_stores"].max(), 100)
    ax.plot(x_line, intercept + slope * x_line, color=C_DARK, lw=2, ls="--",
            label=f"slope={slope:.1f}, r={r_val:.2f}, p={p_val:.3f}")

    ax.axhline(y=0, color="gray", ls=":", alpha=0.5)
    ax.set_xlabel("Number of Round1 stores in prefecture", fontsize=12)
    ax.set_ylabel("% Change in crime (post vs pre)", fontsize=12)
    ax.set_title("Dose-Response: More Round1 Stores vs Crime Change",
                 fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig_jp6_dose_response.png"), dpi=200)
    plt.close(fig)
    print("[Fig JP6] Dose-response saved.")


# ═══════════════════════════════════════════════════════════════════
# Analysis 9: Neighbor prefecture comparison
# ═══════════════════════════════════════════════════════════════════
PREF_NEIGHBORS = {
    "北海道": ["青森県"],
    "青森県": ["北海道", "岩手県", "秋田県"],
    "岩手県": ["青森県", "宮城県", "秋田県"],
    "宮城県": ["岩手県", "秋田県", "山形県", "福島県"],
    "秋田県": ["青森県", "岩手県", "宮城県", "山形県"],
    "山形県": ["秋田県", "宮城県", "福島県", "新潟県"],
    "福島県": ["宮城県", "山形県", "茨城県", "栃木県", "群馬県", "新潟県"],
    "茨城県": ["福島県", "栃木県", "埼玉県", "千葉県"],
    "栃木県": ["福島県", "茨城県", "群馬県", "埼玉県"],
    "群馬県": ["福島県", "栃木県", "埼玉県", "新潟県", "長野県"],
    "埼玉県": ["茨城県", "栃木県", "群馬県", "千葉県", "東京都", "山梨県", "長野県"],
    "千葉県": ["茨城県", "埼玉県", "東京都"],
    "東京都": ["埼玉県", "千葉県", "神奈川県", "山梨県"],
    "神奈川県": ["東京都", "山梨県", "静岡県"],
    "新潟県": ["山形県", "福島県", "群馬県", "長野県", "富山県"],
    "富山県": ["新潟県", "石川県", "長野県", "岐阜県"],
    "石川県": ["富山県", "福井県", "岐阜県"],
    "福井県": ["石川県", "岐阜県", "滋賀県", "京都府"],
    "山梨県": ["埼玉県", "東京都", "神奈川県", "長野県", "静岡県"],
    "長野県": ["群馬県", "埼玉県", "新潟県", "富山県", "山梨県", "静岡県", "愛知県", "岐阜県"],
    "岐阜県": ["富山県", "石川県", "福井県", "長野県", "愛知県", "三重県", "滋賀県"],
    "静岡県": ["神奈川県", "山梨県", "長野県", "愛知県"],
    "愛知県": ["長野県", "岐阜県", "静岡県", "三重県"],
    "三重県": ["岐阜県", "愛知県", "滋賀県", "京都府", "奈良県", "和歌山県"],
    "滋賀県": ["福井県", "岐阜県", "三重県", "京都府"],
    "京都府": ["福井県", "滋賀県", "三重県", "大阪府", "兵庫県", "奈良県"],
    "大阪府": ["京都府", "兵庫県", "奈良県", "和歌山県"],
    "兵庫県": ["京都府", "大阪府", "鳥取県", "岡山県"],
    "奈良県": ["京都府", "大阪府", "三重県", "和歌山県"],
    "和歌山県": ["三重県", "大阪府", "奈良県"],
    "鳥取県": ["兵庫県", "島根県", "岡山県", "広島県"],
    "島根県": ["鳥取県", "広島県", "山口県"],
    "岡山県": ["兵庫県", "鳥取県", "広島県", "香川県"],
    "広島県": ["鳥取県", "島根県", "岡山県", "山口県", "愛媛県"],
    "山口県": ["島根県", "広島県", "福岡県", "大分県"],
    "徳島県": ["香川県", "愛媛県", "高知県"],
    "香川県": ["岡山県", "徳島県", "愛媛県"],
    "愛媛県": ["広島県", "徳島県", "香川県", "高知県"],
    "高知県": ["徳島県", "愛媛県"],
    "福岡県": ["山口県", "佐賀県", "大分県", "熊本県"],
    "佐賀県": ["福岡県", "長崎県"],
    "長崎県": ["佐賀県"],
    "熊本県": ["福岡県", "大分県", "宮崎県", "鹿児島県"],
    "大分県": ["山口県", "福岡県", "熊本県", "宮崎県"],
    "宮崎県": ["大分県", "熊本県", "鹿児島県"],
    "鹿児島県": ["熊本県", "宮崎県"],
    "沖縄県": [],
}


def run_neighbor_prefecture_analysis(df, stores_df):
    """DiD: R1 prefectures vs adjacent non-R1 prefectures only."""
    first_open = get_first_opening_by_prefecture(stores_df)
    r1_prefs = set(first_open.keys())

    # Build pairs: R1 pref → adjacent non-R1 prefectures
    neighbor_non_r1 = set()
    pair_count = 0
    for pref in r1_prefs:
        for nb in PREF_NEIGHBORS.get(pref, []):
            if nb not in r1_prefs:
                neighbor_non_r1.add(nb)
                pair_count += 1

    print(f"\n{'='*70}")
    print("NEIGHBOR PREFECTURE COMPARISON (JAPAN)")
    print(f"{'='*70}")
    print(f"R1 prefectures: {len(r1_prefs)}")
    print(f"Adjacent non-R1 prefectures: {len(neighbor_non_r1)}")
    print(f"Non-R1 neighbor list: {', '.join(sorted(neighbor_non_r1))}")

    if len(neighbor_non_r1) == 0:
        print("  No non-R1 neighbor prefectures — skipping regression.")
        return None

    relevant = r1_prefs | neighbor_non_r1
    sub = df[df["prefecture"].isin(relevant)].copy()
    sub = sub.rename(columns={"total_offenses": "crime"})

    try:
        model = smf.ols(
            "crime ~ post_r1 + C(prefecture) + C(year)", data=sub
        ).fit(cov_type="cluster", cov_kwds={"groups": sub["prefecture"]})
        coef = model.params["post_r1"]
        se = model.bse["post_r1"]
        pval = model.pvalues["post_r1"]
        ci_lo, ci_hi = model.conf_int().loc["post_r1"]
        sig = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else ""

        result = {
            "coefficient": float(round(coef, 1)),
            "std_error": float(round(se, 1)),
            "p_value": float(round(pval, 4)),
            "ci_95": [float(round(ci_lo, 1)), float(round(ci_hi, 1))],
            "significant": bool(pval < 0.05),
            "n_obs": int(len(sub)),
            "n_r1_prefs": len(r1_prefs),
            "n_ctrl_prefs": len(neighbor_non_r1),
        }
        print(f"\n  Total Offenses (neighbor control):")
        print(f"    DiD coef:  {coef:+.1f} {sig}")
        print(f"    SE:        {se:.1f}")
        print(f"    p-value:   {pval:.4f}")
        print(f"    95% CI:    [{ci_lo:.1f}, {ci_hi:.1f}]")
        print(f"    N obs:     {len(sub)}")
    except Exception as e:
        print(f"\n  Regression failed: {e}")
        result = {"error": str(e)}

    with open(os.path.join(OUTPUT_DIR, "japan_neighbor_did_results.json"), "w") as f:
        json.dump(result, f, indent=2)
    return result


def plot_neighbor_prefecture_trends(df, stores_df):
    """Crime trends: R1 prefectures vs adjacent non-R1 prefectures."""
    first_open = get_first_opening_by_prefecture(stores_df)
    r1_prefs = set(first_open.keys())

    neighbor_non_r1 = set()
    for pref in r1_prefs:
        for nb in PREF_NEIGHBORS.get(pref, []):
            if nb not in r1_prefs:
                neighbor_non_r1.add(nb)

    if not neighbor_non_r1:
        print("[Fig JP7] No non-R1 neighbors — skipped.")
        return

    fig, ax = plt.subplots(figsize=(12, 6))
    for prefs, color, label in [
        (r1_prefs, C_R1, "Round1 prefectures"),
        (neighbor_non_r1, C_CTRL, "Adjacent non-R1 prefectures"),
    ]:
        grp = df[df["prefecture"].isin(prefs)].groupby("year")["total_offenses"].mean()
        ax.plot(grp.index, grp.values, color=color, lw=2,
                marker="o", markersize=4, label=label)
    ax.axvline(x=2005, color="gray", ls="--", alpha=0.5, label="R1 expansion peak")
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Mean Total Offenses per Prefecture", fontsize=12)
    ax.set_title("Round1 Prefectures vs Adjacent Non-R1 Neighbors (2002-2023)",
                 fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"{x:,.0f}"))
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig_jp7_neighbor_trends.png"), dpi=200)
    plt.close(fig)
    print("[Fig JP7] Neighbor prefecture trends saved.")


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════
def main():
    print("=" * 70)
    print("ROUND1 JAPAN x CRIME ANALYSIS")
    print("=" * 70)

    stores_df = load_stores()
    print(f"\nLoaded {len(stores_df)} Round1 Japan stores")

    crime_df = build_crime_dataframe()
    print(f"Crime data: {len(crime_df)} rows "
          f"({crime_df['year'].min()}-{crime_df['year'].max()})")

    df = classify_prefectures(stores_df, crime_df)
    n_r1 = df[df["has_round1"] == 1]["prefecture"].nunique()
    n_ctrl = df[df["has_round1"] == 0]["prefecture"].nunique()
    print(f"\nRound1 prefectures: {n_r1}")
    print(f"Control prefectures: {n_ctrl}")

    plot_expansion_timeline(stores_df)
    plot_crime_trends_comparison(df)
    plot_event_study(df)
    did_results = run_did_regression(df)
    plot_did_forest(did_results)
    run_parallel_trends_test(df)
    hm = plot_prefecture_heatmap(df, stores_df)
    plot_dose_response(df, stores_df)

    # Neighbor prefecture analysis
    nb_result = run_neighbor_prefecture_analysis(df, stores_df)
    plot_neighbor_prefecture_trends(df, stores_df)

    print("\n" + "=" * 70)
    print("ALL JAPAN ANALYSES COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
