"""
SVG Stitch-Pattern Renderer (Loom Renderer).

Interprets an SITS9 Deck as a sewing/embroidery pattern.

Coordinate system:
  x = progress along the fabric (time / stitch sequence)
  y = position perpendicular to the fabric edge

The renderer tracks a virtual needle that alternates between the
fabric surface (visible strokes) and the back (dashed strokes).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

import svgwrite

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

# ---------------------------------------------------------------------------
# Rendering state
# ---------------------------------------------------------------------------

@dataclass
class _NeedleState:
    x: float = 0.0
    y: float = 0.0
    on_surface: bool = True
    tension: float = 0.5
    # Collected path segments: (x0, y0, x1, y1, on_surface, tension)
    segments: List[Tuple[float, float, float, float, bool, float]] = field(
        default_factory=list
    )
    # Anchor (knot) positions
    anchors: List[Tuple[float, float]] = field(default_factory=list)
    # Card boundary markers
    card_labels: List[Tuple[float, float, str]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Public renderer
# ---------------------------------------------------------------------------

class SvgRenderer:
    """Render an SITS9 Deck to an SVG sewing pattern."""

    def __init__(
        self,
        scale: float = 20.0,
        surface_color: str = "#c0392b",
        back_color: str = "#95a5a6",
        anchor_color: str = "#2c3e50",
        bg_color: str = "#fdf6e3",
        fabric_color: str = "#faf0dc",
        stroke_width_base: float = 2.0,
        margin: float = 60.0,
    ):
        self.scale = scale
        self.surface_color = surface_color
        self.back_color = back_color
        self.anchor_color = anchor_color
        self.bg_color = bg_color
        self.fabric_color = fabric_color
        self.stroke_width_base = stroke_width_base
        self.margin = margin

    # -- main entry ----------------------------------------------------------

    def render(self, deck: Deck, output_path: str | Path) -> Path:
        output_path = Path(output_path)
        state = self._simulate(deck)
        self._draw(state, deck, output_path)
        return output_path

    # -- simulation ----------------------------------------------------------

    def _simulate(self, deck: Deck) -> _NeedleState:
        st = _NeedleState()
        for card in deck.expanded_cards():
            st.card_labels.append((st.x, st.y, card.name))
            for inst in card.instructions:
                self._exec(inst, st)
        return st

    def _exec(self, inst: Instruction, st: _NeedleState) -> None:
        if isinstance(inst, Forward):
            x0, y0 = st.x, st.y
            st.x += inst.n * self.scale
            st.segments.append((x0, y0, st.x, st.y, st.on_surface, st.tension))

        elif isinstance(inst, Return):
            x0, y0 = st.x, st.y
            st.x -= inst.n * self.scale
            st.segments.append((x0, y0, st.x, st.y, st.on_surface, st.tension))

        elif isinstance(inst, Cross):
            if inst.angle != 0.0:
                rad = math.radians(inst.angle)
                dy = math.sin(rad) * inst.depth * self.scale
                st.y += dy
            st.on_surface = not st.on_surface

        elif isinstance(inst, Tension):
            st.tension = inst.value

        elif isinstance(inst, Anchor):
            st.anchors.append((st.x, st.y))

    # -- drawing -------------------------------------------------------------

    def _draw(
        self, state: _NeedleState, deck: Deck, output_path: Path
    ) -> None:
        if not state.segments:
            xs = [0.0]
            ys = [0.0]
        else:
            xs = [s[0] for s in state.segments] + [s[2] for s in state.segments]
            ys = [s[1] for s in state.segments] + [s[3] for s in state.segments]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        w = max_x - min_x + self.margin * 2
        h = max_y - min_y + self.margin * 2 + 80  # extra for title/legend

        dwg = svgwrite.Drawing(
            str(output_path), size=(f"{w}px", f"{h}px"), viewBox=f"0 0 {w} {h}"
        )

        # background
        dwg.add(dwg.rect((0, 0), (w, h), fill=self.bg_color))
        # fabric area
        fx = self.margin - 10
        fy = self.margin - 10 + 40
        fw = max_x - min_x + 20
        fh = max_y - min_y + 20
        dwg.add(
            dwg.rect(
                (fx - min_x, fy - min_y),
                (fw, fh),
                fill=self.fabric_color,
                rx=4,
                ry=4,
                stroke="#d5c4a1",
                stroke_width=1,
            )
        )

        ox = self.margin - min_x
        oy = self.margin - min_y + 40

        # title
        dwg.add(
            dwg.text(
                deck.title,
                insert=(self.margin, 28),
                font_size="16px",
                font_family="sans-serif",
                font_weight="bold",
                fill="#2c3e50",
            )
        )

        # stitch segments
        for x0, y0, x1, y1, on_surface, tension in state.segments:
            color = self.surface_color if on_surface else self.back_color
            sw = self.stroke_width_base * (0.5 + tension)
            dash = None if on_surface else "4,3"
            opacity = 1.0 if on_surface else 0.5
            extra = {}
            if dash is not None:
                extra["stroke_dasharray"] = dash
            line = dwg.line(
                (x0 + ox, y0 + oy),
                (x1 + ox, y1 + oy),
                stroke=color,
                stroke_width=sw,
                opacity=opacity,
                **extra,
            )
            line["stroke-linecap"] = "round"
            dwg.add(line)

        # needle holes at segment endpoints
        seen_points: set[Tuple[float, float]] = set()
        for x0, y0, x1, y1, *_ in state.segments:
            for px, py in [(x0, y0), (x1, y1)]:
                if (px, py) not in seen_points:
                    seen_points.add((px, py))
                    dwg.add(
                        dwg.circle(
                            (px + ox, py + oy),
                            r=2,
                            fill="#555",
                            opacity=0.6,
                        )
                    )

        # anchors (knots)
        for ax, ay in state.anchors:
            dwg.add(
                dwg.circle(
                    (ax + ox, ay + oy),
                    r=5,
                    fill=self.anchor_color,
                    stroke="white",
                    stroke_width=1.5,
                )
            )

        # card boundary labels
        for lx, ly, label in state.card_labels:
            dwg.add(
                dwg.text(
                    label,
                    insert=(lx + ox, ly + oy - 12),
                    font_size="9px",
                    font_family="monospace",
                    fill="#7f8c8d",
                    text_anchor="start",
                )
            )

        # legend
        ly = h - 30
        dwg.add(dwg.line((20, ly), (40, ly), stroke=self.surface_color, stroke_width=2))
        dwg.add(
            dwg.text("表 (surface)", insert=(45, ly + 4), font_size="10px",
                      font_family="sans-serif", fill="#333")
        )
        dwg.add(
            dwg.line(
                (140, ly), (160, ly),
                stroke=self.back_color, stroke_width=2, stroke_dasharray="4,3",
            )
        )
        dwg.add(
            dwg.text("裏 (back)", insert=(165, ly + 4), font_size="10px",
                      font_family="sans-serif", fill="#333")
        )
        dwg.add(
            dwg.circle((270, ly), r=4, fill=self.anchor_color, stroke="white",
                        stroke_width=1)
        )
        dwg.add(
            dwg.text("玉結び (anchor)", insert=(280, ly + 4), font_size="10px",
                      font_family="sans-serif", fill="#333")
        )

        dwg.save()
