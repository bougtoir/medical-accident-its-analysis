"""Reproducible literature search for the scoping review.

Queries the Europe PMC REST API (public, no key) for open-access reports of
infectious-disease treatment loss-to-follow-up / retention that plot a
time-to-event curve. Writes the hit count and the record list so the PRISMA-ScR
"records identified" number is reproducible rather than asserted.

Eligibility (applied at full-text/figure screening, documented in data/SOURCES.md):
  a published, open-access figure showing a *time-resolved* treatment
  dropout/retention curve (Kaplan-Meier survivor or competing-risk cumulative
  incidence) for an infectious disease, from which a single, cleanly separable
  curve can be digitized. Reports giving only a final cumulative LTFU proportion
  (no curve) are excluded.
"""
import json
import os
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(HERE, "results")
os.makedirs(RESULTS, exist_ok=True)

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

# Infectious-disease treatment retention/LTFU with a time-to-event curve, OA only.
QUERY = (
    '(("loss to follow-up" OR "loss to follow up" OR "lost to follow-up" OR '
    '"retention in care" OR "treatment attrition" OR "disengagement from care") '
    'AND (tuberculosis OR "TB treatment" OR HIV OR "antiretroviral therapy" OR ART) '
    'AND ("Kaplan-Meier" OR "Kaplan Meier" OR "survival curve" OR '
    '"cumulative incidence" OR "time to loss")) '
    'AND (OPEN_ACCESS:Y) AND (PUB_TYPE:"research-article" OR SRC:MED)'
)


def fetch_page(cursor="*", page_size=100):
    params = {
        "query": QUERY,
        "format": "json",
        "pageSize": str(page_size),
        "cursorMark": cursor,
        "resultType": "lite",
    }
    url = BASE + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)


# Retrieve a bounded transparency sample only; the full identified set is far
# too large to screen record-by-record (see manuscript: this is a pragmatic,
# reproducible search, not a completed dual-reviewer scoping review).
SAMPLE_PAGES = 3


def main():
    records, cursor, hit_count = [], "*", None
    for _ in range(SAMPLE_PAGES):
        data = fetch_page(cursor)
        if hit_count is None:
            hit_count = data.get("hitCount", 0)
        batch = data.get("resultList", {}).get("result", [])
        for rec in batch:
            records.append({
                "id": rec.get("id", ""),
                "source": rec.get("source", ""),
                "pmcid": rec.get("pmcid", ""),
                "doi": rec.get("doi", ""),
                "year": rec.get("pubYear", ""),
                "title": (rec.get("title", "") or "").replace("\n", " "),
                "journal": rec.get("journalTitle", ""),
            })
        nxt = data.get("nextCursorMark")
        if not nxt or nxt == cursor or not batch:
            break
        cursor = nxt
        time.sleep(0.3)

    out = os.path.join(RESULTS, "scoping_search.csv")
    import csv
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["search_date", time.strftime("%Y-%m-%d")])
        w.writerow(["europepmc_hit_count", hit_count])
        w.writerow(["transparency_sample_retrieved", len(records)])
        w.writerow(["query", QUERY])
        w.writerow([])
        w.writerow(["id", "source", "pmcid", "doi", "year", "journal", "title"])
        for r in records:
            w.writerow([r["id"], r["source"], r["pmcid"], r["doi"], r["year"],
                        r["journal"], r["title"]])
    print(f"Europe PMC hitCount = {hit_count}; transparency sample {len(records)} rows")
    print("wrote", out)


if __name__ == "__main__":
    main()
