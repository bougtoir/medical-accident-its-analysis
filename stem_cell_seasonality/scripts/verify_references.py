#!/usr/bin/env python3
"""
Automated reference verification against Crossref API, Open Library, and URL checks.

Queries each reference in the manuscript's REFERENCES list against:
- Crossref API (journal articles)
- Open Library API (books)
- HTTP HEAD requests (URLs)

Usage:
    python scripts/verify_references.py

Output:
    - output/reference_audit_report.md  (human-readable)
    - output/reference_audit_report.json (machine-readable)

Requirements:
    - requests (pip install requests)
    - No API key needed (Crossref/Open Library public APIs)

Reproducibility:
    This script produces deterministic output for a given REFERENCES list and
    database state. Results may change if APIs update metadata.
    The JSON report includes a timestamp for traceability.

Severity classification:
    - CRITICAL: Title or first-author mismatch (Crossref found a different paper)
    - WARNING: Volume, pages, or year (>1yr) discrepancy (possible metadata error)
    - INFO: Journal abbreviation vs full name, year +/-1 (expected/acceptable)
"""

import json
import re
import time
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package required. Install: pip install requests")
    sys.exit(1)

# ─── Configuration ────────────────────────────────────────────────────────────
CROSSREF_API = "https://api.crossref.org/works"
OPENLIBRARY_API = "https://openlibrary.org/search.json"
MAILTO = "bougtoir@gmail.com"  # polite pool for faster rate limits
RATE_LIMIT_SECONDS = 1.0  # be polite to API

# ─── Import REFERENCES from the manuscript script ─────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent


def load_references():
    """Parse REFERENCES list from create_perspective_docx.py without executing it."""
    source = SCRIPT_DIR / "create_perspective_docx.py"
    content = source.read_text(encoding="utf-8")

    # Extract the REFERENCES list using regex
    match = re.search(r'^REFERENCES\s*=\s*\[(.*?)\n\]', content, re.MULTILINE | re.DOTALL)
    if not match:
        raise RuntimeError("Could not find REFERENCES list in create_perspective_docx.py")

    block = match.group(1)

    # Use ast.literal_eval on the list
    import ast
    refs_str = "[" + block + "\n]"
    # Remove comments
    lines = refs_str.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
        cleaned_lines.append(line)
    refs_str = '\n'.join(cleaned_lines)

    try:
        refs = ast.literal_eval(refs_str)
    except Exception as e:
        raise RuntimeError(f"Failed to parse REFERENCES: {e}")

    return refs


# ─── Reference Parsing ────────────────────────────────────────────────────────
def parse_reference(ref_str):
    """Extract structured fields from a Vancouver-style reference string."""
    info = {"raw": ref_str}

    # Extract year
    year_match = re.search(r'(\d{4})', ref_str)
    if year_match:
        info["year"] = year_match.group(1)

    # Extract volume/pages pattern: Year;Vol(Issue):Pages
    vol_match = re.search(r'(\d{4});(\d+)\(([^)]+)\):([^.]+)', ref_str)
    if vol_match:
        info["year"] = vol_match.group(1)
        info["volume"] = vol_match.group(2)
        info["issue"] = vol_match.group(3)
        info["pages"] = vol_match.group(4).strip()

    # Extract title (between first ". " after authors and next ". " before journal)
    parts = ref_str.split(". ")
    if len(parts) >= 3:
        info["authors_raw"] = parts[0]
        info["title"] = parts[1]
        info["journal_info"] = ". ".join(parts[2:])
    elif len(parts) == 2:
        info["authors_raw"] = parts[0]
        info["title"] = parts[1]

    # Extract first author surname
    if "authors_raw" in info:
        first_surname = re.match(r'^([A-Za-z\-]+)', info["authors_raw"])
        if first_surname:
            info["first_author_surname"] = first_surname.group(1)

    # Extract journal name (after title, before year)
    journal_match = re.search(r'\.\s+([A-Z][^.]+?)\.\s+\d{4}', ref_str)
    if journal_match:
        info["journal"] = journal_match.group(1).strip()

    # Detect type: book, URL, or article
    publisher_kw = ["Wiley", "Press", "Springer", "Elsevier", "Academic",
                    "McGraw", "Oxford University", "Cambridge University"]
    has_publisher = any(kw in ref_str for kw in publisher_kw)
    has_journal_pattern = bool(re.search(r'\d{4};\d+\(', ref_str))  # Year;Vol(
    if has_publisher and not has_journal_pattern:
        info["type"] = "book"
        for kw in publisher_kw:
            if kw in ref_str:
                info["publisher"] = kw
                break
    elif re.search(r'https?://', ref_str):
        info["type"] = "url"
        url_match = re.search(r'(https?://[^\s,;]+)', ref_str)
        if url_match:
            info["url"] = url_match.group(1).rstrip(".")
    else:
        info["type"] = "article"

    return info


# ─── Journal Abbreviation Handling ────────────────────────────────────────────
def journals_match(ms_journal, cr_journal):
    """Check if manuscript journal (abbreviated) matches Crossref journal (full).

    Returns True if they refer to the same journal (allowing for abbreviation).
    Vancouver style uses NLM abbreviations; Crossref returns full names.
    """
    ms = ms_journal.lower().strip().rstrip(".")
    cr = cr_journal.lower().strip()

    # Direct match
    if ms == cr:
        return True

    # Heuristic: check if all significant words (>=3 chars) in abbreviated form
    # appear in full form (covers most NLM abbreviation patterns)
    ms_words = set(re.findall(r'[a-z]{3,}', ms))
    cr_words = set(re.findall(r'[a-z]{3,}', cr))

    if ms_words and cr_words:
        # If all abbreviated words are found in full form, likely a match
        if ms_words.issubset(cr_words):
            return True
        # Or high overlap relative to the shorter form
        overlap = len(ms_words & cr_words) / len(ms_words) if ms_words else 0
        if overlap >= 0.5:
            return True

    # Check common root words (e.g., "hum" in "human", "reprod" in "reproduction")
    ms_roots = set(re.findall(r'[a-z]{3,}', ms))
    for ms_root in ms_roots:
        if any(cr_word.startswith(ms_root) for cr_word in cr_words):
            continue
        else:
            # One root word not found in any full word — might not match
            return False

    return True


def pages_equivalent(ms_pages, cr_pages):
    """Check if manuscript pages match Crossref pages, accounting for article IDs.

    Some journals use article IDs (e.g., 'deaf008', 'e0236600', 'dmm042317')
    which may differ from Crossref's page field.
    """
    ms = ms_pages.replace("\u2013", "-").replace("\u2014", "-").strip()
    cr = cr_pages.replace("\u2013", "-").replace("\u2014", "-").strip()

    if ms == cr:
        return True

    # If manuscript uses an article ID (alphanumeric, not purely numeric range)
    if re.match(r'^[a-z]+\d+$', ms, re.IGNORECASE):
        # Article ID pattern (e.g., deaf008, e201900534, dmm042317)
        return True

    # If Crossref page contains the manuscript page as substring or vice versa
    if ms in cr or cr in ms:
        return True

    return False


# ─── Open Library Query (Books) ──────────────────────────────────────────────
def query_openlibrary(ref_info):
    """Query Open Library for a book and return match metadata."""
    params = {"limit": 5}

    if "title" in ref_info:
        params["title"] = ref_info["title"]
    if "first_author_surname" in ref_info:
        params["author"] = ref_info["first_author_surname"]

    try:
        resp = requests.get(OPENLIBRARY_API, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {"error": str(e)}

    docs = data.get("docs", [])
    if not docs:
        return {"error": "No results found in Open Library"}

    # Find best match by title similarity
    title_ms = ref_info.get("title", "").lower()
    best = None
    best_score = 0
    for doc in docs[:5]:
        doc_title = (doc.get("title") or "").lower()
        words_ms = set(re.findall(r'\w+', title_ms))
        words_doc = set(re.findall(r'\w+', doc_title))
        if words_ms and words_doc:
            overlap = len(words_ms & words_doc) / max(len(words_ms), len(words_doc))
        else:
            overlap = 0
        if overlap > best_score:
            best_score = overlap
            best = doc

    if not best or best_score < 0.3:
        return {"error": "No matching book found in Open Library"}

    # Collect all known publication years (editions differ)
    publish_years = set()
    if best.get("first_publish_year"):
        publish_years.add(str(best["first_publish_year"]))
    for y in (best.get("publish_year") or []):
        publish_years.add(str(y))

    return {
        "title_openlibrary": best.get("title", ""),
        "authors_openlibrary": best.get("author_name", []),
        "publisher_openlibrary": (best.get("publisher") or [""])[0] if best.get("publisher") else "",
        "year_openlibrary": str(best.get("first_publish_year", "")),
        "all_years": sorted(publish_years),
        "isbn": (best.get("isbn") or [""])[0] if best.get("isbn") else "",
        "title_overlap": best_score,
    }


def compare_book(ref_idx, ref_str, ref_info, ol_result):
    """Compare manuscript book reference against Open Library metadata."""
    issues = []

    if "error" in ol_result:
        return {
            "ref_number": ref_idx + 1,
            "manuscript": ref_str,
            "status": "UNVERIFIED",
            "reason": ol_result["error"],
            "issues": [{"severity": "WARNING", "message": f"Book not found: {ol_result['error']}"}],
            "verification": {"source": "Open Library", "result": ol_result},
        }

    # Title check
    title_overlap = ol_result.get("title_overlap", 0)
    if title_overlap < 0.5:
        issues.append({
            "severity": "WARNING",
            "message": f"Title partial match ({title_overlap:.0%}): "
                       f"OL='{ol_result.get('title_openlibrary', '')}'"
        })

    # Author check
    first_author_ms = ref_info.get("first_author_surname", "").lower()
    authors_ol = ol_result.get("authors_openlibrary", [])
    if first_author_ms and authors_ol:
        found = any(first_author_ms in a.lower() for a in authors_ol)
        if not found:
            issues.append({
                "severity": "WARNING",
                "message": f"Author '{ref_info.get('first_author_surname', '')}' "
                           f"not found in OL authors: {authors_ol[:3]}"
            })

    # Year check — books have multiple editions, so check all known years
    year_ms = ref_info.get("year", "")
    year_ol = ol_result.get("year_openlibrary", "")
    all_years = ol_result.get("all_years", [])
    if year_ms and year_ms in all_years:
        pass  # Exact match with one of the known edition years
    elif year_ms and year_ol and year_ms != year_ol:
        year_diff = abs(int(year_ms) - int(year_ol)) if year_ms.isdigit() and year_ol.isdigit() else 99
        # For books, editions typically span 5-10 years — be lenient
        if year_diff <= 10:
            issues.append({
                "severity": "INFO",
                "message": f"Year: MS={year_ms} vs OL first_publish={year_ol} "
                           f"(editions: {', '.join(all_years[:5])})"
            })
        else:
            issues.append({
                "severity": "WARNING",
                "message": f"Year: MS={year_ms} vs OL={year_ol}"
            })

    # Determine status
    severities = [i["severity"] for i in issues]
    if "CRITICAL" in severities:
        status = "CRITICAL_MISMATCH"
    elif "WARNING" in severities:
        status = "WARNING"
    else:
        status = "MATCH"

    return {
        "ref_number": ref_idx + 1,
        "manuscript": ref_str,
        "status": status,
        "issues": issues,
        "verification": {
            "source": "Open Library",
            "title": ol_result.get("title_openlibrary", ""),
            "authors": ol_result.get("authors_openlibrary", []),
            "year": ol_result.get("year_openlibrary", ""),
            "publisher": ol_result.get("publisher_openlibrary", ""),
            "isbn": ol_result.get("isbn", ""),
        },
    }


# ─── URL Reachability Check ──────────────────────────────────────────────────
def check_url(ref_info):
    """Check if a URL reference is reachable via HTTP HEAD/GET."""
    url = ref_info.get("url", "")
    if not url:
        return {"error": "No URL found in reference"}

    try:
        # Try HEAD first (lightweight)
        resp = requests.head(url, timeout=15, allow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0 (Reference Checker)"})
        if resp.status_code >= 400:
            # Fallback to GET (some servers reject HEAD)
            resp = requests.get(url, timeout=15, allow_redirects=True, stream=True,
                                headers={"User-Agent": "Mozilla/5.0 (Reference Checker)"})
        return {
            "url": url,
            "status_code": resp.status_code,
            "reachable": resp.status_code < 400,
            "final_url": resp.url,
        }
    except requests.exceptions.Timeout:
        return {"url": url, "status_code": None, "reachable": False, "error": "Timeout"}
    except requests.exceptions.ConnectionError as e:
        return {"url": url, "status_code": None, "reachable": False, "error": f"Connection error: {e}"}
    except Exception as e:
        return {"url": url, "status_code": None, "reachable": False, "error": str(e)}


def compare_url(ref_idx, ref_str, ref_info, url_result):
    """Evaluate URL reference reachability."""
    issues = []

    if "error" in url_result and not url_result.get("reachable"):
        issues.append({
            "severity": "WARNING",
            "message": f"URL unreachable: {url_result.get('error', 'unknown error')}"
        })
        return {
            "ref_number": ref_idx + 1,
            "manuscript": ref_str,
            "status": "WARNING",
            "issues": issues,
            "verification": {"source": "HTTP", **url_result},
        }

    if not url_result.get("reachable"):
        issues.append({
            "severity": "WARNING",
            "message": f"URL returned HTTP {url_result.get('status_code')}: {url_result.get('url')}"
        })
        status = "WARNING"
    else:
        status = "MATCH"

    return {
        "ref_number": ref_idx + 1,
        "manuscript": ref_str,
        "status": status,
        "issues": issues,
        "verification": {
            "source": "HTTP",
            "url": url_result.get("url", ""),
            "status_code": url_result.get("status_code"),
            "reachable": url_result.get("reachable", False),
            "final_url": url_result.get("final_url", ""),
        },
    }


# ─── Crossref Query ──────────────────────────────────────────────────────────
def query_crossref(ref_info):
    """Query Crossref for a reference and return top match metadata."""
    query_parts = []
    if "title" in ref_info:
        query_parts.append(ref_info["title"])

    params = {
        "query.bibliographic": " ".join(query_parts)[:500],
        "rows": 3,
        "mailto": MAILTO,
    }

    # Add author filter if available
    if "first_author_surname" in ref_info:
        params["query.author"] = ref_info["first_author_surname"]

    try:
        resp = requests.get(CROSSREF_API, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {"error": str(e)}

    items = data.get("message", {}).get("items", [])
    if not items:
        return {"error": "No results found"}

    # Return top result
    top = items[0]
    result = {
        "doi": top.get("DOI", ""),
        "title_crossref": (top.get("title") or [""])[0],
        "authors_crossref": [],
        "journal_crossref": (top.get("container-title") or [""])[0],
        "volume_crossref": top.get("volume", ""),
        "issue_crossref": top.get("issue", ""),
        "page_crossref": top.get("page", ""),
        "year_crossref": "",
        "score": top.get("score", 0),
        "type": top.get("type", ""),
    }

    # Extract year from published-print or published-online
    for date_field in ["published-print", "published-online", "published", "issued"]:
        if date_field in top:
            date_parts = top[date_field].get("date-parts", [[]])
            if date_parts and date_parts[0]:
                result["year_crossref"] = str(date_parts[0][0])
                break

    # Extract authors
    for author in top.get("author", []):
        family = author.get("family", "")
        given = author.get("given", "")
        if family:
            initials = "".join(w[0] for w in given.split() if w) if given else ""
            result["authors_crossref"].append(f"{family} {initials}")

    # Also check 2nd and 3rd results for better match
    result["alternative_matches"] = []
    for item in items[1:3]:
        alt = {
            "doi": item.get("DOI", ""),
            "title": (item.get("title") or [""])[0],
            "score": item.get("score", 0),
        }
        result["alternative_matches"].append(alt)

    return result


# ─── Comparison Logic ─────────────────────────────────────────────────────────
def compare_reference(ref_idx, ref_str, ref_info, crossref_result):
    """Compare manuscript reference against Crossref metadata.

    Classifies issues by severity:
    - CRITICAL: Title mismatch, first author mismatch (likely wrong paper found)
    - WARNING: Year (>1yr diff), volume, or page discrepancy (possible metadata error)
    - INFO: Journal abbreviation difference, year +/-1 (expected in Vancouver style)
    """
    issues = []  # list of {"severity": ..., "message": ...}

    if "error" in crossref_result:
        return {
            "ref_number": ref_idx + 1,
            "manuscript": ref_str,
            "status": "UNVERIFIED",
            "reason": crossref_result["error"],
            "issues": [{"severity": "INFO", "message": "Could not verify via Crossref API"}],
            "crossref": crossref_result,
        }

    # ── Title check (CRITICAL if mismatch) ──
    title_ms = ref_info.get("title", "").lower().strip()
    title_cr = crossref_result.get("title_crossref", "").lower().strip()
    title_overlap = 1.0

    words_ms = set(re.findall(r'\w+', title_ms))
    words_cr = set(re.findall(r'\w+', title_cr))
    if words_ms and words_cr:
        title_overlap = len(words_ms & words_cr) / max(len(words_ms), len(words_cr))
        if title_overlap < 0.5:
            issues.append({
                "severity": "CRITICAL",
                "message": f"Title mismatch (overlap={title_overlap:.0%}): "
                           f"MS='{ref_info.get('title', '')[:80]}' vs "
                           f"CR='{crossref_result.get('title_crossref', '')[:80]}'"
            })

    # ── First author check ──
    first_author_ms = ref_info.get("first_author_surname", "").lower()
    authors_cr = crossref_result.get("authors_crossref", [])
    if first_author_ms and authors_cr:
        first_author_cr = authors_cr[0].split()[0].lower() if authors_cr[0] else ""
        if first_author_ms and first_author_cr and first_author_ms != first_author_cr:
            severity = "CRITICAL" if title_overlap < 0.7 else "WARNING"
            issues.append({
                "severity": severity,
                "message": f"First author: MS={ref_info.get('first_author_surname', '')} "
                           f"vs Crossref={authors_cr[0] if authors_cr else 'N/A'}"
            })

    # ── Year check (INFO if +/-1, WARNING if >1) ──
    year_ms = ref_info.get("year", "")
    year_cr = crossref_result.get("year_crossref", "")
    if year_ms and year_cr and year_ms != year_cr:
        year_diff = abs(int(year_ms) - int(year_cr)) if year_ms.isdigit() and year_cr.isdigit() else 99
        if year_diff == 1:
            issues.append({
                "severity": "INFO",
                "message": f"Year +/-1 (online-first vs print): MS={year_ms} vs Crossref={year_cr}"
            })
        else:
            issues.append({
                "severity": "WARNING",
                "message": f"Year: MS={year_ms} vs Crossref={year_cr}"
            })

    # ── Volume check (WARNING) ──
    vol_ms = ref_info.get("volume", "")
    vol_cr = crossref_result.get("volume_crossref", "")
    if vol_ms and vol_cr and vol_ms != vol_cr:
        issues.append({
            "severity": "WARNING",
            "message": f"Volume: MS={vol_ms} vs Crossref={vol_cr}"
        })

    # ── Pages check (WARNING, but tolerant of article IDs) ──
    pages_ms = ref_info.get("pages", "")
    pages_cr = crossref_result.get("page_crossref", "")
    if pages_ms and pages_cr and not pages_equivalent(pages_ms, pages_cr):
        issues.append({
            "severity": "WARNING",
            "message": f"Pages: MS={pages_ms} vs Crossref={pages_cr}"
        })

    # ── Journal check (INFO only — abbreviation vs full name is expected) ──
    journal_ms = ref_info.get("journal", "")
    journal_cr = crossref_result.get("journal_crossref", "")
    if journal_ms and journal_cr and not journals_match(journal_ms, journal_cr):
        issues.append({
            "severity": "INFO",
            "message": f"Journal name difference: MS='{journal_ms}' vs Crossref='{journal_cr}'"
        })

    # ── Determine overall status ──
    severities = [i["severity"] for i in issues]
    if "CRITICAL" in severities:
        status = "CRITICAL_MISMATCH"
    elif "WARNING" in severities:
        status = "WARNING"
    elif issues:  # INFO only
        status = "MATCH"  # INFO-level issues are acceptable (abbreviations, +/-1 year)
    else:
        status = "MATCH"

    return {
        "ref_number": ref_idx + 1,
        "manuscript": ref_str,
        "status": status,
        "issues": issues,
        "crossref": {
            "doi": crossref_result.get("doi", ""),
            "title": crossref_result.get("title_crossref", ""),
            "authors": crossref_result.get("authors_crossref", [])[:5],
            "journal": crossref_result.get("journal_crossref", ""),
            "volume": crossref_result.get("volume_crossref", ""),
            "issue": crossref_result.get("issue_crossref", ""),
            "pages": crossref_result.get("page_crossref", ""),
            "year": crossref_result.get("year_crossref", ""),
            "score": crossref_result.get("score", 0),
        },
    }


# ─── Report Generation ────────────────────────────────────────────────────────
def generate_markdown_report(results, timestamp):
    """Generate a human-readable markdown audit report."""
    lines = [
        "# Reference Verification Audit Report",
        "",
        f"**Generated:** {timestamp}",
        f"**Method:** Articles → Crossref API | Books → Open Library API | URLs → HTTP reachability",
        f"**Source:** `scripts/create_perspective_docx.py` REFERENCES list",
        f"**Total references:** {len(results)}",
        "",
    ]

    # Summary
    matches = sum(1 for r in results if r["status"] == "MATCH")
    warnings = sum(1 for r in results if r["status"] == "WARNING")
    critical = sum(1 for r in results if r["status"] == "CRITICAL_MISMATCH")
    unverified = sum(1 for r in results if r["status"] == "UNVERIFIED")

    lines.extend([
        "## Summary",
        "",
        "| Status | Count | Meaning |",
        "|--------|-------|---------|",
        f"| MATCH | {matches} | Verified correct (INFO-level notes only) |",
        f"| WARNING | {warnings} | Possible metadata error (year/vol/pages) |",
        f"| CRITICAL_MISMATCH | {critical} | Crossref found different paper — likely wrong ref |",
        f"| UNVERIFIED | {unverified} | Could not verify (book, API miss) |",
        "",
        "### Severity Legend",
        "",
        "- **CRITICAL**: Title or first-author mismatch → Crossref matched a different paper",
        "- **WARNING**: Volume, pages, or year (>1yr diff) discrepancy → needs manual check",
        "- **INFO**: Journal abbreviation vs full name, year +/-1 → acceptable/expected",
        "",
    ])

    # Details — only show non-MATCH results in detail
    if warnings + critical + unverified > 0:
        lines.extend(["## Issues Requiring Attention", ""])
        for r in results:
            if r["status"] == "MATCH":
                continue
            icon = {"WARNING": "⚠️", "CRITICAL_MISMATCH": "🚨", "UNVERIFIED": "❓"}.get(r["status"], "?")
            lines.append(f"### {icon} Ref {r['ref_number']}: {r['status']}")
            lines.append("")
            lines.append(f"**Manuscript:** {r['manuscript']}")
            lines.append("")

            if r.get("crossref", {}).get("doi"):
                lines.append(f"**Crossref DOI:** https://doi.org/{r['crossref']['doi']}")
                lines.append(f"**Crossref title:** {r['crossref'].get('title', 'N/A')}")
                lines.append(f"**Crossref authors:** {', '.join(r['crossref'].get('authors', [])[:5])}")
                lines.append(f"**Crossref journal:** {r['crossref'].get('journal', 'N/A')}")
                yr = r['crossref'].get('year', '?')
                vol = r['crossref'].get('volume', '?')
                iss = r['crossref'].get('issue', '?')
                pg = r['crossref'].get('pages', '?')
                lines.append(f"**Crossref year;vol(issue):pages:** {yr};{vol}({iss}):{pg}")

            if r["issues"]:
                lines.append("")
                lines.append("**Issues:**")
                for issue in r["issues"]:
                    sev = issue["severity"]
                    msg = issue["message"]
                    lines.append(f"- [{sev}] {msg}")

            lines.append("")
            lines.append("---")
            lines.append("")

    # All results table
    lines.extend(["## All Results (Quick View)", ""])
    lines.append("| # | Status | First Author | Year | Notes |")
    lines.append("|---|--------|--------------|------|-------|")
    for r in results:
        fa = r.get("crossref", {}).get("authors", ["?"])[0] if r.get("crossref", {}).get("authors") else "?"
        yr = r.get("crossref", {}).get("year", "?")
        notes = "; ".join(i["message"][:50] for i in r.get("issues", []) if i["severity"] != "INFO")
        lines.append(f"| {r['ref_number']} | {r['status']} | {fa} | {yr} | {notes[:60]} |")
    lines.append("")

    # Methodology
    lines.extend([
        "## Methodology",
        "",
        "1. Each reference is parsed to extract: first author surname, title, year, volume, pages",
        "2. Reference type detected: article → Crossref API, book → Open Library API, URL → HTTP check",
        "3. **Articles**: Crossref queried with `query.bibliographic` + `query.author`; metadata compared",
        "4. **Books**: Open Library queried with title + author; title/author/year compared",
        "5. **URLs**: HTTP HEAD request to verify reachability (status code < 400)",
        "6. Issues classified by severity: CRITICAL > WARNING > INFO",
        "7. Journal abbreviation differences (NLM vs full name) classified as INFO (acceptable)",
        "8. Article IDs (e.g., 'deaf008', 'e201900534') recognized as valid page identifiers",
        "9. Year differences of exactly +/-1 classified as INFO (online-first vs print)",
        "",
        "### Limitations",
        "",
        "- Crossref coverage is not 100% (some older/non-English journals may be missing)",
        "- Open Library coverage varies; some books may not have entries",
        "- URL reachability may be affected by geoblocking, authentication, or temporary outages",
        "- Author name transliterations may differ between databases",
        "- This script verifies metadata accuracy, NOT whether the citation supports the claim in text",
        "- A MATCH status means the API confirmed the work exists with matching metadata —",
        "  it does NOT verify the full author list beyond the first author",
        "",
        "### Reproducibility",
        "",
        "Re-run: `python scripts/verify_references.py`",
        "",
        "Results are deterministic for a given REFERENCES list and Crossref database state.",
        "Crossref metadata may be updated over time (corrections, retractions).",
        "Commit the JSON/MD reports as audit artifacts alongside the manuscript.",
    ])

    return "\n".join(lines)


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("REFERENCE VERIFICATION SCRIPT")
    print("Articles → Crossref API | Books → Open Library | URLs → HTTP check")
    print("=" * 70)

    # Load references
    refs = load_references()
    print(f"\nLoaded {len(refs)} references from create_perspective_docx.py\n")

    results = []

    for idx, ref_str in enumerate(refs):
        ref_num = idx + 1
        print(f"[{ref_num:2d}/{len(refs)}] Verifying: {ref_str[:70]}...")

        # Parse reference
        ref_info = parse_reference(ref_str)

        # Books: verify via Open Library
        if ref_info.get("type") == "book":
            ol_result = query_openlibrary(ref_info)
            result = compare_book(idx, ref_str, ref_info, ol_result)
            results.append(result)
            icon = "✓" if result["status"] == "MATCH" else "⚠" if result["status"] == "WARNING" else "?"
            print(f"       → {icon} {result['status']} (book, via Open Library)")
            time.sleep(RATE_LIMIT_SECONDS)
            continue

        # URLs: verify reachability
        if ref_info.get("type") == "url":
            url_result = check_url(ref_info)
            result = compare_url(idx, ref_str, ref_info, url_result)
            results.append(result)
            icon = "✓" if result["status"] == "MATCH" else "⚠"
            print(f"       → {icon} {result['status']} (URL, HTTP {url_result.get('status_code', '?')})")
            time.sleep(RATE_LIMIT_SECONDS)
            continue

        # Query Crossref
        crossref_result = query_crossref(ref_info)

        # Compare
        result = compare_reference(idx, ref_str, ref_info, crossref_result)
        results.append(result)

        status_icon = {"MATCH": "✓", "WARNING": "⚠", "CRITICAL_MISMATCH": "✗", "UNVERIFIED": "?"}
        icon = status_icon.get(result["status"], "?")
        print(f"       → {icon} {result['status']}", end="")
        warn_msgs = [i["message"][:50] for i in result["issues"] if i["severity"] != "INFO"]
        if warn_msgs:
            print(f" ({'; '.join(warn_msgs[:2])})")
        else:
            print()

        # Rate limit
        time.sleep(RATE_LIMIT_SECONDS)

    # Generate reports
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    output_dir = SCRIPT_DIR.parent / "output"
    output_dir.mkdir(exist_ok=True)

    # JSON report
    json_report = {
        "timestamp": timestamp,
        "method": "Crossref API (articles) + Open Library (books) + HTTP (URLs) with severity classification",
        "script": "scripts/verify_references.py",
        "total_references": len(refs),
        "summary": {
            "match": sum(1 for r in results if r["status"] == "MATCH"),
            "warning": sum(1 for r in results if r["status"] == "WARNING"),
            "critical_mismatch": sum(1 for r in results if r["status"] == "CRITICAL_MISMATCH"),
            "unverified": sum(1 for r in results if r["status"] == "UNVERIFIED"),
        },
        "results": results,
    }

    json_path = output_dir / "reference_audit_report.json"
    json_path.write_text(json.dumps(json_report, indent=2, ensure_ascii=False))
    print(f"\n✓ JSON report: {json_path}")

    # Markdown report
    md_report = generate_markdown_report(results, timestamp)
    md_path = output_dir / "reference_audit_report.md"
    md_path.write_text(md_report)
    print(f"✓ Markdown report: {md_path}")

    # Print summary
    s = json_report["summary"]
    print(f"\n{'=' * 70}")
    print(f"SUMMARY: {s['match']} MATCH | {s['warning']} WARNING | "
          f"{s['critical_mismatch']} CRITICAL | {s['unverified']} UNVERIFIED")
    print(f"{'=' * 70}")

    # Exit code: 0 if no critical, 1 if any critical mismatch
    if s["critical_mismatch"] > 0:
        sys.exit(2)
    elif s["warning"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
