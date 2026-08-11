#!/usr/bin/env python3
"""Preprocess the PersuasionForGood corpus into CSVs."""
import csv
import json
from pathlib import Path

from convokit import Corpus, download

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


def main():
    corpus_dir = download("persuasionforgood-corpus")
    corpus = Corpus(filename=corpus_dir)

    utterance_rows = []
    dialogue_rows = []

    for conv in corpus.iter_conversations():
        meta = conv.meta
        dialogue_id = meta["dialogue_id"]
        donation_ee = float(meta.get("donation_ee", 0) or 0)
        donation_er = float(meta.get("donation_er", 0) or 0)
        intended = float(meta.get("intended", 0) or 0) if meta.get("intended") is not None else None
        is_annotated = bool(meta.get("is_annotated", False))
        user_er = meta.get("user_er", "")
        user_ee = meta.get("user_ee", "")

        dialogue_rows.append({
            "dialogue_id": dialogue_id,
            "user_er": user_er,
            "user_ee": user_ee,
            "donation_ee": donation_ee,
            "donation_er": donation_er,
            "intended": intended,
            "is_annotated": is_annotated,
            "n_utterances": 0,
            "n_persuader_turns": 0,
            "n_persuadee_turns": 0,
        })

        # Iterate utterances in order and build turn-level features.
        all_turns = list(conv.iter_utterances())
        n_all = len(all_turns)
        persuader_turns = [u for u in all_turns if u.meta.get("role") == 0]
        n_persuader = len(persuader_turns)
        n_persuadee = len([u for u in all_turns if u.meta.get("role") == 1])

        dialogue_rows[-1]["n_utterances"] = n_all
        dialogue_rows[-1]["n_persuader_turns"] = n_persuader
        dialogue_rows[-1]["n_persuadee_turns"] = n_persuadee

        # Pre-calculate persuader-only normalized positions.
        persuader_idx = {id(u): i for i, u in enumerate(persuader_turns)}

        for overall_idx, utt in enumerate(all_turns):
            role = utt.meta.get("role")
            text = utt.text or ""
            word_count = len(text.split())
            text_by_sent = utt.meta.get("text_by_sent", "")
            n_sents = utt.meta.get("n_sents", 0) or 0
            label_1 = json.dumps(utt.meta.get("label_1", []), ensure_ascii=False) if isinstance(utt.meta.get("label_1"), list) else ""
            label_2 = json.dumps(utt.meta.get("label_2", []), ensure_ascii=False) if isinstance(utt.meta.get("label_2"), list) else ""
            sentiment = json.dumps(utt.meta.get("sentiment", {}), ensure_ascii=False) if isinstance(utt.meta.get("sentiment"), dict) else ""

            persuader_turn = persuader_idx.get(id(utt))
            persuader_pos = (persuader_turn / (n_persuader - 1)) if n_persuader > 1 and role == 0 else None
            overall_pos = overall_idx / (n_all - 1) if n_all > 1 else None

            utterance_rows.append({
                "dialogue_id": dialogue_id,
                "utterance_id": utt.id,
                "speaker_id": utt.speaker.id,
                "role": role,
                "overall_turn": overall_idx,
                "overall_position": overall_pos,
                "persuader_turn": persuader_turn,
                "persuader_position": persuader_pos,
                "word_count": word_count,
                "n_sents": n_sents,
                "text": text,
                "label_1": label_1,
                "label_2": label_2,
                "sentiment": sentiment,
            })

    # Write CSVs.
    dialogue_path = DATA_DIR / "persuasion_dialogues.csv"
    with dialogue_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(dialogue_rows[0].keys()))
        writer.writeheader()
        writer.writerows(dialogue_rows)

    utterance_path = DATA_DIR / "persuasion_utterances.csv"
    with utterance_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(utterance_rows[0].keys()))
        writer.writeheader()
        writer.writerows(utterance_rows)

    print(f"Saved {dialogue_path}: {len(dialogue_rows)} dialogues")
    print(f"Saved {utterance_path}: {len(utterance_rows)} utterances")


if __name__ == "__main__":
    main()
