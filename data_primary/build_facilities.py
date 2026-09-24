#!/usr/bin/env python3
"""Build annual facility counts by specialty from the official MHLW
Medical Facility (Dynamic) Survey '病院/診療所の診療科目別にみた施設数（重複計上）'.

Raw sources: data_primary/raw/facilities/facil_YYYY.xls[x] (2008-2024).

Construct: number of facilities declaring each specialty (重複計上 = a facility
offering several specialties is counted under each). Because of this overlap we
do NOT sum subspecialties (that would double-count); we read the published broad
標榜科 row directly for each of the 12 core specialties.

Hospital total per specialty = 一般病院 + 精神科病院 (current-year columns).
Clinic total per specialty = 一般診療所 current-year column.
Outputs hospital-only, clinic-only, and hospital+clinic CSVs.

Years 2004-2007 use a different combined layout ('表6 診療科目別にみた施設数')
and are handled separately (see parse_old()).
"""
import os, re, json, hashlib
import xlrd, openpyxl
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw", "facilities")

CORE = ["内科", "外科", "整形外科", "形成外科", "産婦人科", "小児科", "精神科",
        "眼科", "耳鼻咽喉科", "泌尿器科", "皮膚科", "麻酔科"]

# facility label variants -> core (1:1, published 標榜 rows; no aggregation)
LABELMAP = {
    "内科": "内科", "外科": "外科", "整形外科": "整形外科", "形成外科": "形成外科",
    "産婦人科": "産婦人科", "小児科": "小児科", "精神科": "精神科", "眼科": "眼科",
    "耳鼻いんこう科": "耳鼻咽喉科", "耳鼻咽喉科": "耳鼻咽喉科",
    "泌尿器科": "泌尿器科", "皮膚科": "皮膚科", "麻酔科": "麻酔科",
}


def norm(s):
    return re.sub(r"[\s　]", "", s) if isinstance(s, str) else ""


def rows_from_xlsx(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    for sn in wb.sheetnames:
        ws = wb[sn]
        grid = [list(r) for r in ws.iter_rows(values_only=True)]
        yield sn, grid


def rows_from_xls(path):
    wb = xlrd.open_workbook(path)
    for sn in wb.sheet_names():
        ws = wb.sheet_by_name(sn)
        grid = [[ws.cell_value(r, c) for c in range(ws.ncols)]
                for r in range(ws.nrows)]
        yield sn, grid


def find_table(grids, need_kind):
    """need_kind '病院' or '診療所'. Return the grid whose title has
    <kind> + 診療科目別 + 施設数."""
    for sn, grid in grids:
        for row in grid[:4]:
            for v in row:
                if isinstance(v, str) and need_kind in v and "診療科目別" in v \
                        and "施設数" in v:
                    return grid
    return None


def num(v):
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.replace(",", "").strip()
        if re.fullmatch(r"\d+", s):
            return float(s)
    return None


def col_of(grid, header_kw, header_top=8):
    """column index whose header cell (rows 0..header_top) contains header_kw."""
    for r in range(min(header_top, len(grid))):
        for c, v in enumerate(grid[r]):
            if isinstance(v, str) and header_kw in norm(v):
                return c
    return None


def first_data_col(grid, start_col, label_rows, min_val=0):
    """From start_col rightward, the first column that holds counts in the
    labelled specialty rows. min_val filters out rank/index columns."""
    for c in range(start_col, start_col + 8):
        vals = [num(grid[r][c]) for r in label_rows
                if c < len(grid[r]) and num(grid[r][c]) is not None]
        if len(vals) >= 3 and sorted(vals)[len(vals) // 2] > min_val:
            return c
    return None


def label_rows(grid):
    out = {}
    seen = set()
    for r, row in enumerate(grid):
        for v in row:
            n = norm(v)
            # store the first occurrence of each label (one row per core specialty)
            if n in LABELMAP and r not in out and LABELMAP[n] not in seen:
                out[r] = LABELMAP[n]
                seen.add(LABELMAP[n])
    return out


def parse_hospital(grid):
    lr = label_rows(grid)
    # locate '一般病院' and '精神科病院' header blocks
    gen_c = col_of(grid, "一般病院")
    psy_c = col_of(grid, "精神科病院")
    rows = sorted(lr)
    gen_data = first_data_col(grid, (gen_c or 2) + 0, rows) if gen_c is not None else None
    psy_data = first_data_col(grid, psy_c, rows) if psy_c is not None else None
    res = {}
    for r, core in lr.items():
        g = num(grid[r][gen_data]) if gen_data is not None and gen_data < len(grid[r]) else None
        p = num(grid[r][psy_data]) if psy_data is not None and psy_data < len(grid[r]) else None
        if g is None:
            continue
        res[core] = int(g + (p or 0))
    return res


def parse_clinic(grid):
    lr = label_rows(grid)
    rows = sorted(lr)
    # clinics: single current-year count; skip rank/index cols (min_val=100)
    dc = first_data_col(grid, 2, rows, min_val=100)
    if dc is None:
        return {}
    res = {}
    for r, core in lr.items():
        v = num(grid[r][dc]) if dc < len(grid[r]) else None
        if v is not None:
            res[core] = int(v)
    return res


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def main():
    hosp, clin = {}, {}
    prov = []
    for y in range(2008, 2025):
        for ext in (".xlsx", ".xls"):
            p = os.path.join(RAW, f"facil_{y}{ext}")
            if os.path.exists(p):
                break
        else:
            print("MISSING", y); continue
        reader = rows_from_xlsx if p.endswith(".xlsx") else rows_from_xls
        gh = find_table(list(reader(p)), "病院")
        gc = find_table(list(reader(p)), "診療所")
        hosp[y] = parse_hospital(gh) if gh is not None else {}
        clin[y] = parse_clinic(gc) if gc is not None else {}
        prov.append({"year": y, "file": os.path.basename(p), "sha256": sha256(p),
                     "hospital_specialties": len(hosp[y]),
                     "clinic_specialties": len(clin[y])})
        print(y, "hosp", {k: hosp[y].get(k) for k in CORE})

    def to_df(d):
        years = sorted(d)
        df = pd.DataFrame({"specialty": CORE})
        for y in years:
            df[y] = [d[y].get(s) for s in CORE]
        return df

    # hospital = annual outcome; clinic = only 静態-survey years (every 3rd yr)
    clin = {y: v for y, v in clin.items() if v}
    to_df(hosp).to_csv(os.path.join(HERE, "facilities_hospital_by_specialty.csv"), index=False)
    to_df(clin).to_csv(os.path.join(HERE, "facilities_clinic_by_specialty.csv"), index=False)
    with open(os.path.join(HERE, "provenance_facilities.json"), "w") as f:
        json.dump({"source": "MHLW 医療施設(動態)調査 診療科目別施設数（重複計上）",
                   "note": "hospital: annual 2008-2024 (一般+精神科病院), used as facility "
                           "time-series outcome. clinic: specialty detail only in the "
                           "3-yearly 静態 survey (2008,2011,2014,2017,2020,2023); "
                           "descriptive only. per-standing counts, no subspecialty "
                           "summing (重複計上).", "files": prov},
                  f, ensure_ascii=False, indent=2)
    print("\nclinic years:", sorted(clin))
    print("wrote hospital (annual) + clinic (3-yearly) CSVs")


if __name__ == "__main__":
    main()
