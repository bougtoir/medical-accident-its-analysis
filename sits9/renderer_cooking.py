"""
Cooking Renderer (Kitchen Renderer).

Interprets an SITS9 Deck as a cooking procedure / recipe.

Mapping:
  FWD(n)      → Heat/cook for n time-units
  RET(n)      → Rest/cool for n time-units
  CROSS       → Switch cooking method (grill ↔ simmer ↔ steam)
  TENSION(v)  → Heat level (v=0: off/low, v=1: max)
  ANCHOR      → Taste and season (fix the flavour)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from sits9.core import (
    Anchor,
    Card,
    Cross,
    Deck,
    Forward,
    Instruction,
    Return,
    Tension,
)

METHODS = ["焼く (grill)", "煮る (simmer)", "蒸す (steam)"]

HEAT_LABELS = [
    (0.0, "火を止める (off)"),
    (0.2, "とろ火 (lowest)"),
    (0.4, "弱火 (low)"),
    (0.6, "中火 (medium)"),
    (0.8, "強火 (high)"),
    (1.0, "最強火 (max)"),
]


def _heat_label(v: float) -> str:
    for threshold, label in reversed(HEAT_LABELS):
        if v >= threshold:
            return label
    return HEAT_LABELS[0][1]


@dataclass
class RecipeStep:
    action: str
    duration_min: float
    detail: str
    card_name: str


class CookingRenderer:
    """Render an SITS9 Deck to a cooking recipe (plain text + structured)."""

    def __init__(self, time_unit_minutes: float = 2.0):
        self.time_unit_minutes = time_unit_minutes

    def render(self, deck: Deck, output_path: str | Path) -> Path:
        output_path = Path(output_path)
        steps = self._simulate(deck)
        text = self._format(deck, steps)
        output_path.write_text(text, encoding="utf-8")
        return output_path

    def get_steps(self, deck: Deck) -> List[RecipeStep]:
        return self._simulate(deck)

    def _simulate(self, deck: Deck) -> List[RecipeStep]:
        steps: List[RecipeStep] = []
        method_idx = 0
        heat = 0.5

        for card in deck.expanded_cards():
            for inst in card.instructions:
                if isinstance(inst, Forward):
                    dur = inst.n * self.time_unit_minutes
                    method = METHODS[method_idx % len(METHODS)]
                    steps.append(RecipeStep(
                        action="加熱",
                        duration_min=dur,
                        detail=f"{method}で{_heat_label(heat)}、{dur:.0f}分",
                        card_name=card.name,
                    ))

                elif isinstance(inst, Return):
                    dur = inst.n * self.time_unit_minutes
                    steps.append(RecipeStep(
                        action="休ませる",
                        duration_min=dur,
                        detail=f"火を止めて{dur:.0f}分休ませる（余熱で馴染ませる）",
                        card_name=card.name,
                    ))

                elif isinstance(inst, Cross):
                    method_idx += 1
                    new_method = METHODS[method_idx % len(METHODS)]
                    steps.append(RecipeStep(
                        action="調理法切替",
                        duration_min=0,
                        detail=f"→ {new_method}に切り替える",
                        card_name=card.name,
                    ))

                elif isinstance(inst, Tension):
                    heat = inst.value
                    steps.append(RecipeStep(
                        action="火加減",
                        duration_min=0,
                        detail=f"火加減を{_heat_label(heat)}に調整",
                        card_name=card.name,
                    ))

                elif isinstance(inst, Anchor):
                    steps.append(RecipeStep(
                        action="味見・調味",
                        duration_min=1,
                        detail="味見をして塩梅を整える（ANCHOR: 味の固定点）",
                        card_name=card.name,
                    ))

        return steps

    def _format(self, deck: Deck, steps: List[RecipeStep]) -> str:
        lines = [
            f"# {deck.title} — 料理レンダリング",
            f"# {deck.description}",
            "",
            "=" * 60,
            "  SITS9 料理レシピ",
            "=" * 60,
            "",
        ]
        total_min = sum(s.duration_min for s in steps)
        lines.append(f"調理時間合計: 約{total_min:.0f}分")
        lines.append("")

        for i, step in enumerate(steps, 1):
            card_tag = f"[{step.card_name}]"
            lines.append(f"  {i:2d}. {step.detail}")
            lines.append(f"      {card_tag}")
            lines.append("")

        lines.append("=" * 60)
        lines.append("※ このレシピは音楽・手芸と同一のSITS9カードデッキから")
        lines.append("  自動生成されています。")
        return "\n".join(lines)
