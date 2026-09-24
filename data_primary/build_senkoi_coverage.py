#!/usr/bin/env python3
"""Build senkoi (specialist-trainee) coverage reference table.

Primary sources (data_primary/raw/senkoi/):
  - 000452411.pdf (MHLW): H30 (2018) 専攻医採用数 by specialty, and
    for the H24 medical-license cohort the H26 (3rd year after registration)
    and H28 (5th year after registration) counts by specialty.
  - mhlw_323.pdf (MHLW): 平成27年度 report of physicians in the 3rd to 5th
    year after medical registration by main specialty (H26 survey).

Output:
  - data_primary/senkoi_coverage.csv
  - data_primary/senkoi_coverage_sources.json

The coverage ratio is computed as the number of first-year specialist trainees
(専攻医) divided by the number of physicians in the 3rd-5th year after medical
registration for the same specialty, using the most directly comparable
published counts. The H26 3-5 year stock is the denominator because the
mhlw_323.pdf table explicitly reports "医籍登録後3～5年目" physicians by
specialty; the H30 専攻医 intake is the numerator because it is the first year
of the new specialist-training programme.
"""
import os
import re
import json
import pdfplumber
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw", "senkoi")
OUT_CSV = os.path.join(HERE, "senkoi_coverage.csv")
OUT_JSON = os.path.join(HERE, "senkoi_coverage_sources.json")

CORE = ["内科", "外科", "整形外科", "形成外科", "産婦人科", "小児科", "精神科",
        "眼科", "耳鼻咽喉科", "泌尿器科", "皮膚科", "麻酔科"]

EN = {
    "内科": "Internal medicine",
    "外科": "Surgery",
    "整形外科": "Orthopaedics",
    "形成外科": "Plastic surgery",
    "産婦人科": "Obstetrics & gynaecology",
    "小児科": "Paediatrics",
    "精神科": "Psychiatry",
    "眼科": "Ophthalmology",
    "耳鼻咽喉科": "Otolaryngology",
    "泌尿器科": "Urology",
    "皮膚科": "Dermatology",
    "麻酔科": "Anaesthesiology",
}


def _int(v):
    if not v:
        return None
    s = str(v).replace(",", "").replace(" ", "").replace("\u3000", "").replace("約", "")
    if s in ("-", "ー", "—", ""):
        return None
    try:
        return int(s)
    except ValueError:
        return None


def parse_senkoi_3_5(path):
    """Parse 000452411.pdf and return {specialty: (senkoi, yr3, yr5)}."""
    out = {}
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue
            for row in table:
                if not row or not row[0]:
                    continue
                name = row[0].strip().replace("（※2）", "").replace("\n", " ")
                if name == "合 計":
                    # keep totals separately if needed
                    out["合計"] = (_int(row[1]), _int(row[8]), _int(row[13]))
                    continue
                if name not in CORE and name not in ["病理", "臨床検査", "救急科", "リハビリ", "総合診療"]:
                    continue
                senkoi = _int(row[1])
                yr3 = _int(row[8])
                yr5 = _int(row[13])
                out[name] = (senkoi, yr3, yr5)
    return out


def _clean_name(s):
    s = str(s).replace("\n", "").replace(" ", "").replace("\u3000", "")
    s = re.sub(r"[（(][※＊*][^）)]*[）)]", "", s)
    s = s.replace("診断科", "").replace("臨床検査科", "臨床検査")
    return s.strip()


def _parse_mhlw_323_page(page):
    """Parse one page of mhlw_323.pdf and return (specialty_list, count_list)."""
    text = page.extract_text() or ""
    if "医籍登録後３～５年目" not in text and "医籍登録後3～5年目" not in text:
        return None, None

    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
    # Find the header line(s) and the national row.
    header_idx = None
    national_idx = None
    for i, ln in enumerate(lines):
        if ln.startswith("臨床研修医"):
            header_idx = i
        if ln.startswith("全 国"):
            national_idx = i
    if header_idx is None or national_idx is None:
        return None, None

    # The header may wrap across two lines. On page 5 the rotated header cell
    # "リハビリテーション" appears on the line above the main header row, but it
    # is the last specialty in the table. We append it if it is missing.
    header = lines[header_idx]
    if header_idx > 0 and "臨床研修医" not in lines[header_idx - 1]:
        prev = lines[header_idx - 1].strip()
        if re.search(r"[\u4e00-\u9fff科]", prev):
            # Append to the end unless it is already present.
            if prev not in header:
                header = header + " " + prev

    # Drop "臨床研修医" and any "総数" token; the remaining tokens are specialty names.
    header = re.sub(r"臨床研修医", "", header)
    header = re.sub(r"総数", "", header)
    header_tokens = [t for t in re.split(r"[\s　]+", header) if t]

    # National row: drop prefix "全 国" and the first count (募集定員上限/総数 total), keep the rest.
    national_line = lines[national_idx]
    national_line = re.sub(r"^全\s*国", "", national_line)
    national_parts = re.split(r"[\s　]+", national_line.strip())
    # The first numeric token is the total ceiling count; specialty counts follow.
    counts = []
    for p in national_parts:
        n = _int(p)
        if n is not None:
            counts.append(n)
    if not counts:
        return None, None
    # First count is the overall ceiling; remaining counts correspond to specialties.
    specialty_counts = counts[1:]

    # Clean specialty names and merge split tokens such as "眼 科" -> "眼科".
    raw_names = [_clean_name(t) for t in header_tokens]
    raw_names = [t for t in raw_names if t and t not in ("臨床研修医", "総数")]
    names = []
    i = 0
    while i < len(raw_names):
        if i + 1 < len(raw_names) and not raw_names[i].endswith("科") and raw_names[i + 1] == "科":
            names.append(raw_names[i] + "科")
            i += 2
        else:
            names.append(raw_names[i])
            i += 1

    return names, specialty_counts


def parse_mhlw_323(path):
    """Parse mhlw_323.pdf and return {specialty: physicians_3_5yr}."""
    out = {}
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            names, counts = _parse_mhlw_323_page(page)
            if not names or not counts:
                continue
            for name, count in zip(names, counts):
                if name not in CORE:
                    continue
                out[name] = count
    return out


def main():
    senkoi_path = os.path.join(RAW, "000452411.pdf")
    mhlw_path = os.path.join(RAW, "mhlw_323.pdf")

    senkoi = parse_senkoi_3_5(senkoi_path)
    pool = parse_mhlw_323(mhlw_path)

    rows = []
    for s in CORE:
        senkoi_count, yr3, yr5 = senkoi.get(s, (None, None, None))
        pool_count = pool.get(s)
        coverage = (senkoi_count / pool_count * 100) if senkoi_count and pool_count else None
        rows.append({
            "specialty_ja": s,
            "specialty_en": EN[s],
            "senkoi_2018": senkoi_count,
            "physicians_3_5_yr_2014": pool_count,
            "yr3_2012_cohort": yr3,
            "yr5_2012_cohort": yr5,
            "coverage_pct": round(coverage, 1) if coverage is not None else None,
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    sources = {
        "senkoi_source": {
            "file": "data_primary/raw/senkoi/000452411.pdf",
            "url": "https://www.mhlw.go.jp/content/10803000/000452411.pdf",
            "description": "MHLW, H30 (2018) newly admitted specialist trainees (専攻医) and H24-cohort 3rd/5th-year physician counts by specialty.",
            "accessed": "2026-08-15",
        },
        "pool_source": {
            "file": "data_primary/raw/senkoi/mhlw_323.pdf",
            "url": "https://www.mhlw.go.jp/file/06-Seisakujouhou-10800000-Iseikyoku/323.pdf",
            "description": "MHLW, 平成27年度 report of physicians 3-5 years after medical registration by main specialty (H26 survey, 2014).",
            "accessed": "2026-08-15",
        },
        "notes": "Coverage = 2018 first-year specialist trainees / 2014 physicians 3-5 years after registration, by specialty.",
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(sources, f, ensure_ascii=False, indent=2)

    print("wrote", OUT_CSV)
    print("wrote", OUT_JSON)


if __name__ == "__main__":
    main()
