#!/usr/bin/env python3
"""Download and preprocess the CyberAgentAILab/salestalk-dataset."""
import csv
import json
import re
import zipfile
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

DATASET_URL = "https://github.com/CyberAgentAILab/salestalk-dataset/archive/refs/heads/main.zip"
ZIP_PATH = DATA_DIR / "salestalk-dataset_main.zip"
EXTRACT_DIR = DATA_DIR / "salestalk-dataset_main"
JSONL_PATH = EXTRACT_DIR / "salestalk-dataset-main" / "data" / "japanese-salestalk-dataset_v1.json"


def download_data():
    if not ZIP_PATH.exists():
        print(f"Downloading {DATASET_URL} ...")
        r = requests.get(DATASET_URL)
        r.raise_for_status()
        ZIP_PATH.write_bytes(r.content)
    if not JSONL_PATH.exists():
        with zipfile.ZipFile(ZIP_PATH) as z:
            z.extractall(EXTRACT_DIR)
    return JSONL_PATH


def clean_text(text: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def count_words(text: str) -> int:
    """Simple whitespace-based word count (mostly useful for English tokens)."""
    return len(text.split())


def count_chars(text: str) -> int:
    """Count non-whitespace, non-punctuation characters as a Japanese verbosity proxy."""
    return len(re.sub(r"\s+|[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]", "", text))


def main():
    jsonl_path = download_data()

    dialogues = []
    utterances = []

    with jsonl_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            dialogue_id = d["dialogue_id"]
            sales_id = d.get("sales_id", "")
            user_id = d.get("user_id", "")

            before = None
            after = None
            for ev in d.get("user_dialogue_evals", []):
                if ev["label"] == "before_purchase_intention":
                    before = ev["answer"]
                elif ev["label"] == "after_purchase_intention":
                    after = ev["answer"]
            change = (after - before) if before is not None and after is not None else None

            # Parse timestamps and compute elapsed seconds.
            raw_utts = [u for u in d["utterances"] if u.get("speaker") in ("sales", "user")]
            timestamps = []
            for u in raw_utts:
                ts = u.get("timestamp")
                if ts:
                    try:
                        dt = datetime.fromisoformat(ts)
                        timestamps.append(dt)
                    except Exception:
                        timestamps.append(None)
                else:
                    timestamps.append(None)

            start_dt = next((t for t in timestamps if t is not None), None)
            elapsed = [(t - start_dt).total_seconds() if t and start_dt else None for t in timestamps]
            max_elapsed = max([e for e in elapsed if e is not None], default=None)

            sales_utts = [u for u in raw_utts if u.get("speaker") == "sales"]
            n_sales = len(sales_utts)
            n_user = len([u for u in raw_utts if u.get("speaker") == "user"])

            dialogues.append({
                "dialogue_id": dialogue_id,
                "sales_id": sales_id,
                "user_id": user_id,
                "before_purchase_intention": before,
                "after_purchase_intention": after,
                "purchase_intention_change": change,
                "n_utterances": len(raw_utts),
                "n_sales_turns": n_sales,
                "n_user_turns": n_user,
                "duration_seconds": max_elapsed,
            })

            sales_idx = {id(u): i for i, u in enumerate(sales_utts)}

            for overall_idx, u in enumerate(raw_utts):
                speaker = u.get("speaker")
                text = clean_text(u.get("message", ""))
                word_count = count_words(text)
                char_count = count_chars(text)

                sales_turn = sales_idx.get(id(u))
                sales_pos = (sales_turn / (n_sales - 1)) if n_sales > 1 and speaker == "sales" else None
                overall_pos = overall_idx / (len(raw_utts) - 1) if len(raw_utts) > 1 else None
                elapsed_sec = elapsed[overall_idx]
                time_pos = (elapsed_sec / max_elapsed) if max_elapsed and elapsed_sec is not None else None

                # Encode user evals (only user turns have these).
                evals = u.get("user_utterance_evals", []) or []
                eval_map = {ev["label"]: ev["answer"] for ev in evals}

                utterances.append({
                    "dialogue_id": dialogue_id,
                    "utterance_id": u.get("utterance_id"),
                    "speaker": speaker,
                    "overall_turn": overall_idx,
                    "overall_position": overall_pos,
                    "sales_turn": sales_turn,
                    "sales_position": sales_pos,
                    "elapsed_seconds": elapsed_sec,
                    "time_position": time_pos,
                    "word_count": word_count,
                    "char_count": char_count,
                    "text": text,
                    "continuing_dialogue": eval_map.get("CONTINUING_DIALOGUE"),
                    "providing_information": eval_map.get("PROVIDING_INFORMATION"),
                    "goal_acceptance": eval_map.get("GOAL_ACCEPTANCE"),
                })

    dialogue_path = DATA_DIR / "cyberagent_dialogues.csv"
    with dialogue_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(dialogues[0].keys()))
        writer.writeheader()
        writer.writerows(dialogues)

    utterance_path = DATA_DIR / "cyberagent_utterances.csv"
    with utterance_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(utterances[0].keys()))
        writer.writeheader()
        writer.writerows(utterances)

    print(f"Saved {dialogue_path}: {len(dialogues)} dialogues")
    print(f"Saved {utterance_path}: {len(utterances)} utterances")


if __name__ == "__main__":
    main()
