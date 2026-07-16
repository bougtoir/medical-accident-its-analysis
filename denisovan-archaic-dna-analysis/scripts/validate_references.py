"""Verify manuscript references against Crossref or PubMed."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import requests

from ajba_content import REFERENCES


OUTPUT_PATH = Path("docs/ahg_submission/reference_validation.csv")
HEADERS = {
    "User-Agent": "AHG-reference-validation/1.0 (mailto:bougtoir@gmail.com)"
}


def expected_title(reference: str) -> str:
    match = re.search(r"“([^”]+)”", reference)
    return match.group(1) if match else reference


def crossref_record(doi: str) -> tuple[str, str]:
    response = requests.get(
        f"https://api.crossref.org/works/{doi}",
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()
    message = response.json()["message"]
    return message["title"][0], message.get("URL", f"https://doi.org/{doi}")


def pubmed_record(pmid: str) -> tuple[str, str]:
    response = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
        params={"db": "pubmed", "id": pmid, "retmode": "json"},
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()
    record = response.json()["result"][pmid]
    return record["title"].rstrip("."), f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"


def normalized(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def main() -> None:
    rows = []
    for number, reference in enumerate(REFERENCES, 1):
        expected = expected_title(reference)
        doi_match = re.search(r"https://doi\.org/(.+)\.$", reference)
        if doi_match:
            identifier = doi_match.group(1)
            canonical, url = crossref_record(identifier)
            registry = "Crossref"
        else:
            raise ValueError(f"Reference has no DOI: {reference}")
        expected_words = set(normalized(expected).split())
        canonical_words = set(normalized(canonical).split())
        overlap = len(expected_words & canonical_words) / max(len(expected_words), 1)
        rows.append(
            {
                "reference_number": number,
                "registry": registry,
                "identifier": identifier,
                "expected_title": expected,
                "canonical_title": canonical,
                "title_word_overlap": round(overlap, 3),
                "status": "verified" if overlap >= 0.8 else "review",
                "url": url,
            }
        )
    output = pd.DataFrame(rows)
    if not output["status"].eq("verified").all():
        raise RuntimeError(output[output["status"] != "verified"].to_string(index=False))
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT_PATH, index=False)
    print(f"Verified {len(output)} references and wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
