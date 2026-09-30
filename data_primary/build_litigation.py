#!/usr/bin/env python3
"""Build annual litigation counts by specialty from official Supreme Court
'医事関係訴訟事件（地裁）の診療科目別既済件数' tables.

Raw sources (data_primary/raw/litigation/):
  text-extractable PDFs:
    lit_2017mtg_spec.pdf   -> 平成23-29 (2011-2017)   [Wayback, iji committee]
    lit_2022stat_2015-2021.pdf -> 平成27-令和3 (2015-2021)
    lit_2025stat_2017-2024.pdf -> 平成29-令和6 (2017-2024)
  image-only PDFs (OCR w/ tesseract-jpn, verified against overlaps):
    lit_2012snap_spec.pdf  -> 平成20-22 (2008-2010)   [Wayback 804005]
    lit_2009_2011.pdf      -> 平成21-23 (2009-2011)   [Wayback 804009]

Specialty rows appear in a fixed order:
  内科 / 小児科 / 精神科(神経科) / 皮膚科 / 外科 / 整形外科 / 形成外科 /
  泌尿器科 / 産婦人科 / 眼科 / 耳鼻咽喉科 / 歯科 / 麻酔科 / その他 / 合計
We keep the 12 core clinical specialties (drop 歯科, その他, 合計).

Overlapping years across text sources are cross-checked. Any disagreement is
printed and recorded in provenance_litigation.json (source, value) rather than
silently dropped; the value used is then taken from the highest-priority source
(lower priority number wins). The one known disagreement is 2017 internal
medicine (179 in the 2022/2024/2025 statistics vs 181 in the 2017 committee
minutes); the current released figure 179 is used and the mismatch is retained
in provenance. The 2008-2010 scanned tables are digitised (image_transcription
.csv) and validated against the 2011 text overlap, which must match exactly or
the build aborts.
"""
import os, re, json, hashlib, subprocess
import pdfplumber
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw", "litigation")

CORE = ["内科", "外科", "整形外科", "形成外科", "産婦人科", "小児科", "精神科",
        "眼科", "耳鼻咽喉科", "泌尿器科", "皮膚科", "麻酔科"]

# ordered rows as printed
ROWS = ["内科", "小児科", "精神科", "皮膚科", "外科", "整形外科", "形成外科",
        "泌尿器科", "産婦人科", "眼科", "耳鼻咽喉科", "歯科", "麻酔科", "その他"]


def wareki_to_year(s):
    s = s.replace(" ", "")
    m = re.search(r"平成(\d+|元)年", s)
    if m:
        n = 1 if m.group(1) == "元" else int(m.group(1))
        return 1988 + n
    m = re.search(r"令和(\d+|元)年", s)
    if m:
        n = 1 if m.group(1) == "元" else int(m.group(1))
        return 2018 + n
    return None


def parse_text_pdf(path):
    """-> {year: {core: count}} from a text-extractable specialty table."""
    with pdfplumber.open(path) as pdf:
        text = ""
        for page in pdf.pages:
            t = page.extract_text() or ""
            # prefer a proper TABLE page (has 合計 total row + 内科)
            if ("合 計" in t or "合計" in t) and ("内 科" in t or "内科" in t):
                text = t
                break
        if not text:
            for page in pdf.pages:
                t = page.extract_text() or ""
                if "内 科" in t or "内科" in t:
                    text = t
                    break
    # normalize full-width digits -> half-width
    text = text.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    lines = text.splitlines()
    joined = text.replace(" ", "")
    # (a) range title '（<start>～<end>）'
    years = None
    m = re.search(r"[（(]((?:平成|令和)(?:\d+|元)年)[～~]((?:平成|令和)(?:\d+|元)年)",
                  joined)
    if m:
        y0, y1 = wareki_to_year(m.group(1)), wareki_to_year(m.group(2))
        years = list(range(y0, y1 + 1))
    else:
        # (b) fallback: consecutive range from min..max of all year tokens
        toks = re.findall(r"(?:平成|令和)(?:\d+|元)年", text)
        ys = sorted({wareki_to_year(t) for t in toks})
        if ys:
            years = list(range(ys[0], ys[-1] + 1))
    if not years:
        raise ValueError(f"no year range title in {path}")
    out = {y: {} for y in years}
    for base in ROWS:
        # find the line for this specialty
        pat = "".join(base[:2])  # first 2 chars enough to locate
        found = None
        for ln in lines:
            comp = ln.replace(" ", "").replace("　", "")
            key = base.replace("科", "")
            # match by known label prefixes
            if base == "内科" and comp.startswith("内科"):
                found = ln
            elif base == "精神科" and comp.startswith("精神科"):
                found = ln
            elif base != "内科" and base != "精神科" and comp.startswith(base):
                found = ln
            if found:
                break
        if not found:
            raise ValueError(f"row {base} not found in {path}")
        nums = [int(x) for x in re.findall(r"\d+", found)]
        nums = nums[-len(years):]
        if len(nums) != len(years):
            raise ValueError(f"row {base}: {len(nums)} nums vs {len(years)} years in {path}")
        for y, v in zip(years, nums):
            if base in CORE:
                out[y][base] = v
    return {y: v for y, v in out.items() if v}


def ocr_image_pdf(path, expected_years):
    """OCR a scanned specialty table. Returns {year:{core:count}}.
    Uses fixed row order; OCR numbers per row, cross-checked externally."""
    png = path.replace(".pdf", "_ocr")
    subprocess.run(["pdftoppm", "-png", "-r", "300", path, png], check=True)
    img = png + "-1.png"
    txt = subprocess.run(["tesseract", img, "stdout", "-l", "jpn+eng",
                          "--psm", "6"], capture_output=True, text=True).stdout
    lines = [l for l in txt.splitlines() if l.strip()]
    out = {y: {} for y in expected_years}
    for base in ROWS:
        cand = None
        for ln in lines:
            comp = re.sub(r"[\s　]", "", ln)
            head = comp[:6]
            if base == "内科" and head.startswith("内"):
                cand = ln
            elif base == "小児科" and "児" in head:
                cand = ln
            elif base == "外科" and head.startswith("外"):
                cand = ln
            elif base == "整形外科" and "整形" in comp:
                cand = ln
            elif base == "形成外科" and "形成" in comp:
                cand = ln
            elif base == "精神科" and "精神" in comp:
                cand = ln
            elif base == "皮膚科" and ("皮" in head):
                cand = ln
            elif base == "泌尿器科" and ("泌" in comp or "尿" in comp):
                cand = ln
            elif base == "産婦人科" and ("産婦" in comp or "婦人" in comp):
                cand = ln
            elif base == "眼科" and head.startswith("眼"):
                cand = ln
            elif base == "耳鼻咽喉科" and ("耳鼻" in comp or "咽喉" in comp):
                cand = ln
            elif base == "麻酔科" and "麻酔" in comp:
                cand = ln
            if cand:
                break
        if cand and base in CORE:
            nums = [int(x) for x in re.findall(r"\d+", cand)]
            nums = nums[-len(expected_years):]
            if len(nums) == len(expected_years):
                for y, v in zip(expected_years, nums):
                    out[y][base] = v
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def main():
    # (file, priority) - lower priority number wins on overlap
    src = [
        ("lit_2025stat_2017-2024.pdf", 1),   # 2017-2024 (2024 provisional)
        ("lit_2024mtg_spec.pdf", 2),          # 2017-2023
        ("lit_2022stat_2015-2021.pdf", 2),    # 2015-2021
        ("lit_2017mtg_spec.pdf", 2),          # 2011-2017
    ]
    parsed = {}
    prov = []
    for fn, pri in src:
        p = os.path.join(RAW, fn)
        if not os.path.exists(p):
            print("MISSING", fn); continue
        data = parse_text_pdf(p)
        parsed[fn] = (data, pri)
        prov.append({"file": fn, "kind": "text", "years": sorted(data),
                     "sha256": sha256(p)})
        print(fn, "->", {y: data[y] for y in sorted(data)})

    # image-only years 2008-2011: load transcription of official scanned tables
    tcsv = os.path.join(RAW, "image_transcription.csv")
    tdf = pd.read_csv(tcsv, comment="#")
    trans = {int(y): {r["specialty"]: int(r[y]) for _, r in tdf.iterrows()}
             for y in tdf.columns if y != "specialty"}
    # validate: 2011 transcription must equal text-source (lit_2017mtg) 2011
    ref = parsed["lit_2017mtg_spec.pdf"][0][2011]
    for s in CORE:
        if trans[2011][s] != ref[s]:
            raise SystemExit(f"transcription 2011 {s}={trans[2011][s]} != "
                             f"text {ref[s]}: FIX before use")
    print("\n[validation] image transcription 2011 == text source 2011: OK")
    parsed["image_transcription.csv"] = ({y: trans[y] for y in (2008, 2009, 2010)}, 2)
    prov.append({"file": "image_transcription.csv", "kind": "digitised-scan",
                 "years": [2008, 2009, 2010], "sha256": sha256(tcsv),
                 "validated": "2011 overlap == lit_2017mtg_spec.pdf"})

    # cross-check overlaps between TEXT sources (authoritative); report mismatches
    text_sources = {fn: d for fn, (d, pri) in parsed.items()
                    if fn.endswith(".pdf") and pri <= 2}
    mism = []
    items = list(text_sources.items())
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            (fa, da), (fb, db) = items[i], items[j]
            for y in set(da) & set(db):
                for s in CORE:
                    va, vb = da[y].get(s), db[y].get(s)
                    if va is not None and vb is not None and va != vb:
                        mism.append((y, s, fa, va, fb, vb))
    if mism:
        print("\n*** TEXT-SOURCE MISMATCHES ***")
        for m in mism:
            print(m)

    # assemble final series (lowest priority number wins)
    years = sorted({y for d, _ in parsed.values() for y in d})
    final = {}
    for y in years:
        best_pri = 99
        for fn, (d, pri) in parsed.items():
            if y in d and pri < best_pri:
                best_pri = pri
                final[y] = d[y]
    df = pd.DataFrame({"specialty": CORE})
    for y in years:
        df[y] = [final[y].get(s) for s in CORE]
    out_csv = os.path.join(HERE, "litigation_by_specialty.csv")
    df.to_csv(out_csv, index=False)
    print("\n", df.to_string(index=False))

    with open(os.path.join(HERE, "provenance_litigation.json"), "w") as f:
        json.dump({"source": "最高裁判所 医事関係訴訟委員会 診療科目別既済件数",
                   "note": "annual; broad specialties as published; 2024 provisional "
                           "(速報値); overlaps cross-checked between sources",
                   "mismatches": mism, "files": prov}, f,
                  ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
