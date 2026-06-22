#!/usr/bin/env python3
"""
Demo: National anthems → SITS9 → SVG + MIDI + Recipe.

Four anthems with contrasting musical characteristics:
  - Kimigayo (Japan)       — pentatonic, slow, narrow range
  - La Marseillaise (France) — march, wide dynamics, modulation
  - Star-Spangled Banner (US) — wide range (1.5 oct), leaping
  - Hino Nacional (Brazil)  — syncopation, long melodic lines

Each anthem is encoded as a SITS9 Deck reflecting its melodic
contour, tension profile, and rhythmic character.
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

OUT_DIR = Path(__file__).parent / "output" / "anthems"


# ---------------------------------------------------------------------------
# Kimigayo (君が代) — Japan
# ---------------------------------------------------------------------------
# Pentatonic (D E F# A B), slow 4/4, narrow range (~octave),
# gentle stepwise motion. Key of D (= MIDI 62).
# Melodic contour: starts on tonic, gentle ascent to 5th, descent,
# rise to climax on 6th degree, gentle fall back to tonic.

def build_kimigayo() -> Deck:
    # Pentatonic palette: steps of 1, 2, 3 only (no 4th/7th)
    cards = []
    surface = True

    phrases = [
        # (name, dir, n, tension, chord, degree, root, notes, loom_hint, tone_hint)
        ("君が代は",    "anchor", 0, 0.15, "D",  "I",   62, [62, 66, 69],
         "玉結び — 静かな始まり", "I: 悠然としたトニック"),
        ("千代に",      "fwd",    2, 0.25, "Em", "ii",  64, [64, 67, 71],
         "2目前進 — 緩やかな上昇", "ii: 一歩上昇、控えめ"),
        ("八千代に",    "fwd",    3, 0.35, "F#m","iii", 66, [66, 69, 73],
         "3目前進 — 詠嘆の広がり", "iii: ペンタトニック上昇"),
        ("さざれ石の",  "ret",    2, 0.20, "D",  "I",   62, [62, 66, 69],
         "2目回帰 — 静かな帰還", "I: トニック回帰、内省"),
        ("巌となりて",  "fwd",    3, 0.45, "A",  "V",   69, [69, 73, 64],
         "3目前進 — クライマックスへ", "V: 穏やかな頂点"),
        ("苔の",        "ret",    2, 0.30, "Bm", "vi",  71, [71, 62, 66],
         "2目回帰 — 下降開始", "vi: 平行短調、余韻"),
        ("むすまで",    "ret",    3, 0.15, "D",  "I",   62, [62, 66, 69],
         "3目回帰 — 静寂への着地", "I: 最終解決、玉留め"),
        ("(ending)",    "anchor", 0, 0.10, "D",  "I",   62, [62, 66, 69],
         "玉留め — 永遠の余韻", "I: 消え入るように終止"),
    ]

    for name, direction, dist, tens, chord, deg, root, notes, lh, th in phrases:
        instructions = []
        cross_angle = 15.0 if surface else -15.0  # gentle zigzag

        if direction == "anchor":
            instructions.append(Anchor())
            instructions.append(Tension(value=tens))
        elif direction == "fwd":
            instructions.append(Tension(value=tens))
            instructions.append(Forward(n=dist))
            instructions.append(Cross(angle=cross_angle))
            surface = not surface
        elif direction == "ret":
            instructions.append(Tension(value=tens))
            instructions.append(Return(n=dist))
            instructions.append(Cross(angle=cross_angle))
            surface = not surface

        cards.append(Card(
            name=name,
            instructions=instructions,
            chord_label=chord,
            scale_degree=deg,
            root_midi=root,
            chord_notes_midi=notes,
            stitch_type="back_stitch" if direction == "ret" else "running",
            loom_hint=lh,
            tone_hint=th,
        ))

    return Deck(
        title="Kimigayo (君が代) — 五音音階の静謐",
        description=(
            "日本国歌「君が代」をSITS9で記述。\n"
            "ペンタトニック制約（FWD n∈{1,2,3}）、低TENSION、\n"
            "穏やかなCROSS角度（±15°）が和の美意識を反映。"
        ),
        cards=cards,
        bpm=54,           # very slow, meditative
        key_root=62,      # D4
        stitch_unit_mm=5.0,  # wide stitch spacing (unhurried)
    )


# ---------------------------------------------------------------------------
# La Marseillaise — France
# ---------------------------------------------------------------------------
# March tempo, C major, dramatic dynamics (pp→ff), wide leaps,
# frequent modulation between major/minor. Key of C (= MIDI 60).

def build_marseillaise() -> Deck:
    cards = []
    surface = True

    phrases = [
        ("Allons enfants",    "anchor", 0, 0.60, "C",  "I",   60, [60, 64, 67],
         "力強い玉結び", "I: 行進曲の号令"),
        ("de la Patrie",      "fwd",    5, 0.75, "G",  "V",   67, [67, 71, 62],
         "5目前進 — 突撃", "V: ドミナント跳躍"),
        ("Le jour de gloire", "fwd",    4, 0.90, "Am", "vi",  69, [69, 60, 64],
         "4目前進 — 高揚", "vi: 短調への転換、緊張最大"),
        ("est arrive!",       "ret",    7, 0.50, "F",  "IV",  65, [65, 69, 60],
         "7目回帰 — 劇的な帰還", "IV: サブドミナント急降下"),
        ("Contre nous",       "fwd",    6, 0.85, "Dm", "ii",  62, [62, 65, 69],
         "6目前進 — 再突撃", "ii: 敵への対峙"),
        ("de la tyrannie",    "ret",    3, 0.70, "G",  "V",   67, [67, 71, 62],
         "3目半返し — 怒りの振動", "V: 不安定なドミナント"),
        ("Aux armes!",        "fwd",    7, 0.95, "C",  "I",   60, [60, 64, 67],
         "7目前進 — 最大の跳躍", "I: ff、武器を取れ！"),
        ("Marchons!",         "anchor", 0, 0.80, "C",  "I",   60, [60, 64, 67],
         "玉留め — 行進の固定", "I: 行進リズムの確立"),
    ]

    for name, direction, dist, tens, chord, deg, root, notes, lh, th in phrases:
        instructions = []
        cross_angle = 45.0 if surface else -45.0  # sharp zigzag

        if direction == "anchor":
            instructions.append(Anchor())
            instructions.append(Tension(value=tens))
        elif direction == "fwd":
            instructions.append(Tension(value=tens))
            instructions.append(Forward(n=dist))
            instructions.append(Cross(angle=cross_angle))
            surface = not surface
        elif direction == "ret":
            instructions.append(Tension(value=tens))
            instructions.append(Return(n=dist))
            instructions.append(Cross(angle=cross_angle))
            surface = not surface

        cards.append(Card(
            name=name,
            instructions=instructions,
            chord_label=chord,
            scale_degree=deg,
            root_midi=root,
            chord_notes_midi=notes,
            stitch_type="back_stitch" if direction == "ret" else "running",
            loom_hint=lh,
            tone_hint=th,
        ))

    return Deck(
        title="La Marseillaise — 行進曲の激情",
        description=(
            "フランス国歌「ラ・マルセイエーズ」をSITS9で記述。\n"
            "大きなFWD/RET振幅、高TENSION、急角度CROSS（±45°）が\n"
            "行進曲の劇的ダイナミクスを反映。"
        ),
        cards=cards,
        bpm=120,          # march tempo
        key_root=60,      # C4
        stitch_unit_mm=3.0,  # tight stitch (energetic)
    )


# ---------------------------------------------------------------------------
# Star-Spangled Banner — United States
# ---------------------------------------------------------------------------
# Wide range (1.5 octaves, Bb3-F5), leaping intervals (6ths, octaves),
# 3/4 time, dramatic arc. Key of Bb (= MIDI 58).

def build_star_spangled() -> Deck:
    cards = []
    surface = True

    phrases = [
        ("Oh say can you see",  "anchor", 0, 0.40, "Bb", "I",   58, [58, 62, 65],
         "玉結び — 問いかけの開始", "I: 穏やかな問い"),
        ("by the dawn's",       "fwd",    6, 0.55, "Eb", "IV",  63, [63, 67, 58],
         "6目前進 — 大きな跳躍", "IV: 6度上昇"),
        ("early light",         "ret",    4, 0.35, "Bb", "I",   58, [58, 62, 65],
         "4目回帰 — 着地", "I: 降下して安定"),
        ("What so proudly",     "fwd",    5, 0.60, "F",  "V",   65, [65, 69, 60],
         "5目前進 — 誇り", "V: ドミナント上昇"),
        ("we hailed",           "fwd",    3, 0.70, "Gm", "vi",  67, [67, 58, 62],
         "3目前進 — さらに上昇", "vi: 短調の色彩"),
        ("the rockets'",        "fwd",    7, 0.90, "Eb", "IV",  63, [63, 67, 58],
         "7目前進 — 最大跳躍、ロケット", "IV: オクターブ跳躍、クライマックス"),
        ("red glare",           "ret",    5, 0.75, "Bb", "I",   58, [58, 62, 65],
         "5目回帰 — 赤の残光", "I: 降下、まだ緊張"),
        ("land of the free",    "fwd",    8, 0.95, "F",  "V",   65, [65, 69, 60],
         "8目前進 — 最高音への到達", "V: 最高音F5、自由の頂点"),
        ("home of the brave",   "ret",    6, 0.30, "Bb", "I",   58, [58, 62, 65],
         "6目回帰 — 壮大な着地", "I: 最終解決、着地"),
        ("(ending)",            "anchor", 0, 0.20, "Bb", "I",   58, [58, 62, 65],
         "玉留め — 余韻", "I: 終止"),
    ]

    for name, direction, dist, tens, chord, deg, root, notes, lh, th in phrases:
        instructions = []
        cross_angle = 40.0 if surface else -40.0  # bold zigzag

        if direction == "anchor":
            instructions.append(Anchor())
            instructions.append(Tension(value=tens))
        elif direction == "fwd":
            instructions.append(Tension(value=tens))
            instructions.append(Forward(n=dist))
            instructions.append(Cross(angle=cross_angle))
            surface = not surface
        elif direction == "ret":
            instructions.append(Tension(value=tens))
            instructions.append(Return(n=dist))
            instructions.append(Cross(angle=cross_angle))
            surface = not surface

        cards.append(Card(
            name=name,
            instructions=instructions,
            chord_label=chord,
            scale_degree=deg,
            root_midi=root,
            chord_notes_midi=notes,
            stitch_type="back_stitch" if direction == "ret" else "running",
            loom_hint=lh,
            tone_hint=th,
        ))

    return Deck(
        title="Star-Spangled Banner — 跳躍と自由",
        description=(
            "米国国歌「星条旗」をSITS9で記述。\n"
            "大きなFWD(n)値（最大8）、広い音域、\n"
            "大胆なCROSS角度（±40°）がダイナミックな旋律を反映。"
        ),
        cards=cards,
        bpm=84,           # moderate 3/4
        key_root=58,      # Bb3
        stitch_unit_mm=3.5,
    )


# ---------------------------------------------------------------------------
# Hino Nacional Brasileiro — Brazil
# ---------------------------------------------------------------------------
# 4/4 with syncopation, long flowing melodies, key of Bb,
# rhythmic irregularity, extended phrases.

def build_hino_nacional() -> Deck:
    cards = []
    surface = True

    phrases = [
        ("Ouviram do Ipiranga", "anchor", 0, 0.50, "Bb", "I",  58, [58, 62, 65],
         "玉結び — 宣言の開始", "I: 堂々とした開始"),
        ("as margens placidas", "fwd",    4, 0.45, "Eb", "IV", 63, [63, 67, 58],
         "4目前進 — 流れるような上昇", "IV: シンコペーションの波"),
        ("de um povo heroico",  "fwd",    3, 0.65, "F",  "V",  65, [65, 69, 60],
         "3目前進 — 英雄的な前進", "V: ドミナントへの到達"),
        ("o brado retumbante",  "ret",    2, 0.55, "Gm", "vi", 67, [67, 58, 62],
         "2目回帰 — シンコペーション", "vi: リズムのずれ、短調"),
        ("e o sol da liberdade", "fwd",   5, 0.75, "Eb", "IV", 63, [63, 67, 58],
         "5目前進 — 自由の太陽", "IV: 長いメロディライン"),
        ("em raios fulgidos",   "fwd",    2, 0.70, "Cm", "ii", 60, [60, 63, 67],
         "2目前進 — 光線の煌めき", "ii: 不規則な間隔"),
        ("brilhou no ceu",      "ret",    4, 0.40, "F",  "V",  65, [65, 69, 60],
         "4目回帰 — 空への回帰", "V: 降下、まだ流動的"),
        ("da Patria nesse",     "fwd",    3, 0.60, "Bb", "I",  58, [58, 62, 65],
         "3目前進 — 祖国の呼びかけ", "I: トニック回帰"),
        ("instante",            "ret",    3, 0.35, "Bb", "I",  58, [58, 62, 65],
         "3目回帰 — 瞬間の固定", "I: 最終解決"),
        ("(ending)",            "anchor", 0, 0.30, "Bb", "I",  58, [58, 62, 65],
         "玉留め — 悠然とした終止", "I: リタルダンド"),
    ]

    for name, direction, dist, tens, chord, deg, root, notes, lh, th in phrases:
        instructions = []
        cross_angle = 25.0 if surface else -25.0  # moderate, flowing

        if direction == "anchor":
            instructions.append(Anchor())
            instructions.append(Tension(value=tens))
        elif direction == "fwd":
            instructions.append(Tension(value=tens))
            instructions.append(Forward(n=dist))
            instructions.append(Cross(angle=cross_angle))
            surface = not surface
        elif direction == "ret":
            instructions.append(Tension(value=tens))
            instructions.append(Return(n=dist))
            instructions.append(Cross(angle=cross_angle))
            surface = not surface

        cards.append(Card(
            name=name,
            instructions=instructions,
            chord_label=chord,
            scale_degree=deg,
            root_midi=root,
            chord_notes_midi=notes,
            stitch_type="back_stitch" if direction == "ret" else "running",
            loom_hint=lh,
            tone_hint=th,
        ))

    return Deck(
        title="Hino Nacional Brasileiro — シンコペーションの流れ",
        description=(
            "ブラジル国歌をSITS9で記述。\n"
            "不規則なFWD間隔、中程度のCROSS角度（±25°）、\n"
            "長いカード列がシンコペーションと流麗な旋律を反映。"
        ),
        cards=cards,
        bpm=100,          # moderate, flowing
        key_root=58,      # Bb3
        stitch_unit_mm=4.0,
    )


# ---------------------------------------------------------------------------
# Main: generate all four anthems
# ---------------------------------------------------------------------------

ANTHEMS = [
    ("kimigayo",       build_kimigayo),
    ("marseillaise",   build_marseillaise),
    ("star_spangled",  build_star_spangled),
    ("hino_nacional",  build_hino_nacional),
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    svg_renderer = SvgRenderer()
    midi_renderer = MidiRenderer()
    cooking_renderer = CookingRenderer()

    for slug, builder in ANTHEMS:
        deck = builder()
        print(f"\n{'='*60}")
        print(f"  {deck.title}")
        print(f"{'='*60}")

        # JSON
        json_path = OUT_DIR / f"{slug}_deck.json"
        json_path.write_text(deck.to_json(), encoding="utf-8")
        print(f"  Deck JSON  → {json_path}")

        # SVG
        svg_path = svg_renderer.render(deck, OUT_DIR / f"{slug}_stitch.svg")
        print(f"  SVG stitch → {svg_path}")

        # MIDI
        midi_path = midi_renderer.render(deck, OUT_DIR / f"{slug}_music.mid")
        print(f"  MIDI music → {midi_path}")

        # Recipe
        recipe_path = cooking_renderer.render(deck, OUT_DIR / f"{slug}_recipe.txt")
        print(f"  Recipe     → {recipe_path}")

        # PNG (via cairosvg if available)
        try:
            import cairosvg
            png_path = OUT_DIR / f"{slug}_stitch.png"
            cairosvg.svg2png(
                url=str(OUT_DIR / f"{slug}_stitch.svg"),
                write_to=str(png_path),
            )
            print(f"  PNG        → {png_path}")
        except ImportError:
            print("  PNG        → (cairosvg not available, skipped)")

        # Print deck structure
        print(f"\n  Cards ({len(deck.cards)}):")
        for i, card in enumerate(deck.cards):
            ops = " → ".join(inst.type.name for inst in card.instructions)
            print(f"    {i}: {card.name:22s} [{ops}]")

    print(f"\nAll anthem outputs → {OUT_DIR}/")


if __name__ == "__main__":
    main()
