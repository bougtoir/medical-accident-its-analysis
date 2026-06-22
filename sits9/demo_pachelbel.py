#!/usr/bin/env python3
"""
Demo: Pachelbel Canon chord progression → SITS9 → SVG + MIDI + Recipe.

Pachelbel's Canon uses the progression:
  D – A – Bm – F#m – G – D – G – A
  (I – V – vi – iii – IV – I – IV – V)

This is the archetypical "返し縫い" (back-stitch) progression:
forward motion (I→V) followed by stepwise return (vi→iii→IV→I),
then a re-advance (IV→V) that overlaps with the starting territory.

We encode each chord as an SITS9 Card with:
  - FWD/RET reflecting the root-motion direction
  - CROSS at each chord boundary (needle passes through fabric)
  - TENSION reflecting harmonic tension (V=high, I=low)
  - ANCHOR on the tonic (I) chords
"""

from pathlib import Path

from sits9.core import (
    Anchor,
    Card,
    Cross,
    Deck,
    Forward,
    Return,
    Tension,
)
from sits9.renderer_cooking import CookingRenderer
from sits9.renderer_midi import MidiRenderer
from sits9.renderer_svg import SvgRenderer

# D major: D=62, E=64, F#=66, G=67, A=69, B=71, C#=73
# Chord voicings (MIDI note numbers)
CHORDS = {
    "D":   {"root": 62, "notes": [62, 66, 69],       "degree": "I",   "tension": 0.2},
    "A":   {"root": 69, "notes": [69, 73, 64],       "degree": "V",   "tension": 0.8},
    "Bm":  {"root": 71, "notes": [71, 62, 66],       "degree": "vi",  "tension": 0.5},
    "F#m": {"root": 66, "notes": [66, 69, 73],       "degree": "iii", "tension": 0.4},
    "G":   {"root": 67, "notes": [67, 71, 62],       "degree": "IV",  "tension": 0.3},
}

# Pachelbel progression with SITS9 instruction logic
PROGRESSION = [
    # (chord_name, direction, distance, stitch_description, music_description)
    ("D",   "anchor",  0, "玉結び — 糸を布に固定",           "I: トニック確立"),
    ("A",   "fwd",     5, "5目前進、裏へ — 離脱",            "V: ドミナント、上方への跳躍"),
    ("Bm",  "fwd",     2, "2目前進、表へ — 頂点",            "vi: 平行短調、最遠点"),
    ("F#m", "ret",     5, "5目回帰、裏へ — 返し縫い開始",    "iii: 回帰開始、下行"),
    ("G",   "fwd",     1, "1目前進、表へ — 半返し",          "IV: サブドミナント、一時停止"),
    ("D",   "ret",     5, "5目回帰 — 元の針穴に重ねる",      "I: トニック帰還、重なり"),
    ("G",   "fwd",     3, "3目前進、裏へ — 再出発",          "IV: 再びサブドミナント"),
    ("A",   "fwd",     2, "2目前進、表へ — ループ準備",      "V: ドミナント、ループ頭へ"),
]


def build_deck() -> Deck:
    cards: list[Card] = []

    surface = True  # track current side for angle direction
    for chord_name, direction, distance, loom_hint, tone_hint in PROGRESSION:
        ch = CHORDS[chord_name]
        instructions = []

        # Alternate angle to create visible zig-zag between surface and back
        cross_angle = 30.0 if surface else -30.0

        if direction == "anchor":
            instructions.append(Anchor())
            instructions.append(Tension(value=ch["tension"]))
        elif direction == "fwd":
            instructions.append(Tension(value=ch["tension"]))
            instructions.append(Forward(n=distance))
            instructions.append(Cross(angle=cross_angle))
            surface = not surface
        elif direction == "ret":
            instructions.append(Tension(value=ch["tension"]))
            instructions.append(Return(n=distance))
            instructions.append(Cross(angle=cross_angle))
            surface = not surface

        card = Card(
            name=f'{chord_name} ({ch["degree"]})',
            instructions=instructions,
            chord_label=chord_name,
            scale_degree=ch["degree"],
            root_midi=ch["root"],
            chord_notes_midi=ch["notes"],
            stitch_type="back_stitch" if direction == "ret" else "running",
            loom_hint=loom_hint,
            tone_hint=tone_hint,
        )
        cards.append(card)

    return Deck(
        title="Pachelbel Canon — 返し縫いの進行",
        description=(
            "パッヘルベルのカノン（I-V-vi-iii-IV-I-IV-V）を\n"
            "SITS9 で記述。同一のカードデッキから\n"
            "刺し子パターン（SVG）と音楽（MIDI）を同時生成する。"
        ),
        cards=cards,
        bpm=72,          # Canon is stately
        key_root=62,     # D4
        stitch_unit_mm=4.0,
    )


def main() -> None:
    out_dir = Path(__file__).parent / "output"
    out_dir.mkdir(exist_ok=True)

    deck = build_deck()

    # Save the deck as JSON (the "punch cards")
    json_path = out_dir / "pachelbel_deck.json"
    json_path.write_text(deck.to_json(), encoding="utf-8")
    print(f"Deck JSON  → {json_path}")

    # Render SVG (loom)
    svg_renderer = SvgRenderer()
    svg_path = svg_renderer.render(deck, out_dir / "pachelbel_stitch.svg")
    print(f"SVG 刺繍   → {svg_path}")

    # Render MIDI (music box)
    midi_renderer = MidiRenderer()
    midi_path = midi_renderer.render(deck, out_dir / "pachelbel_music.mid")
    print(f"MIDI 音楽  → {midi_path}")

    # Render cooking recipe (kitchen)
    cooking_renderer = CookingRenderer()
    recipe_path = cooking_renderer.render(deck, out_dir / "pachelbel_recipe.txt")
    print(f"料理レシピ → {recipe_path}")

    # Also generate a 2-loop version
    deck_loop = build_deck()
    deck_loop.title = "Pachelbel Canon — 返し縫い × 2 loops"
    for card in deck_loop.cards:
        card.repeat = 2

    svg_renderer.render(deck_loop, out_dir / "pachelbel_stitch_2loops.svg")
    midi_renderer.render(deck_loop, out_dir / "pachelbel_music_2loops.mid")
    print("2-loop versions generated.")

    print("\nDeck structure:")
    for i, card in enumerate(deck.cards):
        ops = " → ".join(inst.type.name for inst in card.instructions)
        print(f"  Card {i}: {card.name:15s}  [{ops}]")
        print(f"           loom: {card.loom_hint}")
        print(f"           tone: {card.tone_hint}")


if __name__ == "__main__":
    main()
