#!/usr/bin/env python3
"""
Build the full AI/ML researcher cohort from OpenAlex using the list API.

This is an alternative to the sampled cohort in cohort_extraction.py. It streams
all works in the target subfield and year range through the OpenAlex cursor
paginator, writes them to a local SQLite database, and then classifies every
author who appears in at least one work with a mappable country affiliation.

Usage:
    python src/extract_full_cohort.py
    FULL=1 bash reproduce.sh   # after the cohort.csv has been written
"""

import argparse
import json
import math
import os
import sqlite3
import sys
import time
from collections import defaultdict
from pathlib import Path

import pandas as pd

# Make cohort_extraction helpers importable
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cohort_extraction import (
    ABROAD_WINDOW,
    CAREER_START_MAX,
    CAREER_START_MIN,
    DROPOUT_LATEST_YEAR,
    HIT_WINDOW,
    MIN_WORKS,
    classify_author,
    estimate_rates,
    load_group_mapping,
    load_origin_overrides,
)
from openalex_client import OpenAlexBudgetExhausted, OpenAlexClient

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
COHORT_DIR = DATA_DIR / "cohort"


def setup_db(db_path):
    """Create the works and author_works tables."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-2000000")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS works (
            id TEXT PRIMARY KEY,
            year INTEGER,
            data TEXT
        ) WITHOUT ROWID
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS author_works (
            author_id TEXT,
            work_id TEXT,
            PRIMARY KEY (author_id, work_id)
        ) WITHOUT ROWID
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_aw_author ON author_works(author_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_w_year ON works(year)")
    return conn


def reduce_work(w):
    """Keep only the fields needed by classify_author."""
    reduced = {
        "id": w.get("id"),
        "publication_year": w.get("publication_year"),
        "authorships": [],
        "citation_normalized_percentile": w.get("citation_normalized_percentile"),
    }
    for auth in w.get("authorships", []):
        author = auth.get("author") or {}
        reduced_auth = {
            "author": {
                "id": author.get("id"),
                "display_name": author.get("display_name"),
            },
            "author_position": auth.get("author_position"),
            "institutions": [
                {"country_code": inst.get("country_code")}
                for inst in auth.get("institutions", [])
            ],
        }
        reduced["authorships"].append(reduced_auth)
    return reduced


def author_id_key(raw_id):
    if not raw_id:
        return None
    return raw_id.split("/")[-1]


def has_mappable_country(w, a2g):
    """Return True if at least one authorship institution has a known country."""
    for auth in w.get("authorships", []):
        for inst in auth.get("institutions", []):
            if inst.get("country_code") in a2g:
                return True
    return False


def load_state(state_path):
    """Load the saved cursor or start fresh.  A saved cursor of 'DONE' means
    the API fetch has already completed."""
    if state_path.exists():
        with open(state_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"cursor": "*", "pages": 0, "works": 0, "author_rows": 0}


def save_state(state_path, state):
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f)


def fetch_and_store(client, conn, a2g, state, state_path, subfield_id, start_year,
                    end_year, per_page, pages_per_commit, max_pages, delay):
    """Stream all works through the OpenAlex cursor paginator and store in SQLite."""
    base_filter = (
        f"publication_year:{start_year}-{end_year},"
        f"topics.subfield.id:{subfield_id}"
    )
    base_params = {
        "filter": base_filter,
        "select": "id,publication_year,authorships,citation_normalized_percentile",
        "per-page": per_page,
    }

    cursor = state["cursor"]
    if cursor == "DONE":
        print("API fetch already marked complete; skipping fetch.")
        return state["pages"], state["works"], state["author_rows"]

    pages_done = state["pages"]
    works_done = state["works"]
    rows_done = state["author_rows"]
    start_time = time.time()
    batch_works = []
    batch_authors = []

    # Helper to flush the current batch to the DB and persist state.
    def flush_and_save(next_cursor):
        nonlocal batch_works, batch_authors, rows_done
        conn.executemany(
            "INSERT OR IGNORE INTO works (id, year, data) VALUES (?, ?, ?)",
            batch_works,
        )
        conn.executemany(
            "INSERT OR IGNORE INTO author_works (author_id, work_id) VALUES (?, ?)",
            batch_authors,
        )
        conn.commit()
        rows_done += len(batch_authors)
        batch_works.clear()
        batch_authors.clear()
        state.update({"cursor": next_cursor, "pages": pages_done,
                      "works": works_done, "author_rows": rows_done})
        save_state(state_path, state)

    try:
        while True:
            if max_pages and pages_done >= max_pages:
                print(f"Reached max_pages={max_pages}")
                break

            page = client.get("works", {**base_params, "cursor": cursor})
            results = page.get("results", [])
            pages_done += 1

            for w in results:
                # Skip works with no mappable country affiliation; we cannot
                # assign their authors to a civilisation group.
                if not has_mappable_country(w, a2g):
                    continue

                reduced = reduce_work(w)
                wid = reduced["id"]
                year = reduced["publication_year"]
                batch_works.append((wid, year, json.dumps(reduced, ensure_ascii=False)))

                # Record every author on this work so that later works for the
                # same author can be grouped together, even if some works have
                # missing affiliation metadata.
                seen_authors = set()
                for auth in w.get("authorships", []):
                    aid = author_id_key((auth.get("author") or {}).get("id"))
                    if aid and aid not in seen_authors:
                        seen_authors.add(aid)
                        batch_authors.append((aid, wid))

            works_done += len(results)
            next_cursor = page.get("meta", {}).get("next_cursor")

            if pages_done % pages_per_commit == 0:
                flush_and_save(next_cursor or "DONE")
                elapsed = time.time() - start_time
                rate = pages_done / elapsed if elapsed else 0
                print(f"  pages={pages_done}, works={works_done}, "
                      f"author_rows={rows_done}, elapsed={elapsed:.1f}s, "
                      f"rate={rate:.2f} pg/s, next_cursor={'yes' if next_cursor else 'no'}")

            if not next_cursor:
                break
            cursor = next_cursor

            # Be polite. The OpenAlex client already sleeps between calls when
            # self.delay > 0, but we keep a small extra guard here.
            if delay:
                time.sleep(delay)
    except OpenAlexBudgetExhausted:
        flush_and_save(cursor)
        raise

    # Final flush for any partial batch and mark fetch as done.
    flush_and_save("DONE")
    print(f"Fetch complete: {pages_done} pages, {works_done} works, "
          f"{rows_done} author_works rows.")
    return pages_done, works_done, rows_done


def classify_all_authors(conn, a2g, min_works, overrides, batch_size=500):
    """Classify every author with at least min_works AI/ML works."""
    # Update module-level constants that classify_author reads at call time.
    import cohort_extraction as ce
    ce.MIN_WORKS = min_works

    cur = conn.cursor()
    cur.execute(
        "SELECT author_id, COUNT(*) as c FROM author_works GROUP BY author_id HAVING c >= ?",
        (min_works,),
    )
    author_ids = [row[0] for row in cur.fetchall()]
    print(f"Classifying {len(author_ids)} authors with at least {min_works} works ...")

    rows = []
    total = len(author_ids)
    start = time.time()
    for i in range(0, total, batch_size):
        batch = author_ids[i:i + batch_size]
        placeholders = ",".join(["?"] * len(batch))
        cur.execute(
            f"""SELECT aw.author_id, w.year, w.data
                FROM author_works aw
                JOIN works w ON aw.work_id = w.id
                WHERE aw.author_id IN ({placeholders})
                ORDER BY aw.author_id, w.year, w.id""",
            batch,
        )
        works_by_author = defaultdict(list)
        for aid, year, data in cur:
            w = json.loads(data)
            w["publication_year"] = year
            works_by_author[aid].append(w)

        for aid in batch:
            works = works_by_author.get(aid, [])
            row = classify_author(aid, works, a2g, origin_override=overrides.get(aid))
            if row:
                rows.append(row)

        if (i // batch_size + 1) % 10 == 0 or i + batch_size >= total:
            elapsed = time.time() - start
            pct = (i + len(batch)) / total * 100
            print(f"  classified {i + len(batch)}/{total} ({pct:.1f}%) "
                  f"-> {len(rows)} cohort rows, elapsed={elapsed:.1f}s")

    print(f"Classification complete: {len(rows)} cohort rows from {total} candidate authors.")
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--subfield-id", default="subfields/1702")
    parser.add_argument("--start-year", type=int, default=2000)
    parser.add_argument("--end-year", type=int, default=2023)
    parser.add_argument("--min-works", type=int, default=2)
    parser.add_argument("--output-dir", default=str(COHORT_DIR))
    parser.add_argument("--db-path", default=str(CACHE_DIR / "full_cohort.db"))
    parser.add_argument("--state-path", default=str(CACHE_DIR / "full_cohort_state.json"))
    parser.add_argument("--per-page", type=int, default=200)
    parser.add_argument("--delay", type=float, default=0.05)
    parser.add_argument("--pages-per-commit", type=int, default=10)
    parser.add_argument("--max-pages", type=int, default=0,
                        help="Stop after this many pages (for testing).")
    parser.add_argument("--classify-batch-size", type=int, default=500)
    parser.add_argument("--resume", action="store_true",
                        help="Resume from the cursor stored in --state-path.")
    parser.add_argument("--no-fetch", action="store_true",
                        help="Skip the API fetch and only classify from the existing DB.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = Path(args.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    state_path = Path(args.state_path)

    a2g, _ = load_group_mapping()
    overrides = load_origin_overrides()
    target_codes = set(a2g.keys())
    print(f"Loaded mapping for {len(target_codes)} country codes.")

    conn = setup_db(db_path)

    state = load_state(state_path)
    if not args.no_fetch:
        client = OpenAlexClient(delay=args.delay, cache_dir=None)
        try:
            fetch_and_store(
                client, conn, a2g, state, state_path,
                args.subfield_id, args.start_year, args.end_year,
                args.per_page, args.pages_per_commit, args.max_pages, args.delay,
            )
        except OpenAlexBudgetExhausted as e:
            print(f"ERROR: {e}")
            print("Add credits or wait for the daily reset and rerun with --resume.")
            sys.exit(1)
    else:
        print("Skipping API fetch, classifying from existing DB.")

    cohort = classify_all_authors(
        conn, a2g, args.min_works, overrides, batch_size=args.classify_batch_size
    )
    cohort_path = output_dir / "cohort.csv"
    cohort.to_csv(cohort_path, index=False, encoding="utf-8-sig")
    print(f"Cohort saved to {cohort_path} ({len(cohort)} rows)")

    rates = estimate_rates(cohort)
    rates_path = output_dir / "transition_rates.csv"
    rates.to_csv(rates_path, index=False, encoding="utf-8-sig")
    print(f"Transition rates saved to {rates_path}")
    print(rates.to_string(index=False))

    conn.close()


if __name__ == "__main__":
    main()
