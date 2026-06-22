"""
SITS9 core data model.

Five primitive instructions, combined into Cards, assembled into a Deck.
The same Deck can be rendered as a sewing pattern (SVG) or as music (MIDI).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional


# ---------------------------------------------------------------------------
# Primitive instructions
# ---------------------------------------------------------------------------

class InstructionType(Enum):
    FWD = auto()
    RET = auto()
    CROSS = auto()
    TENSION = auto()
    ANCHOR = auto()


@dataclass(frozen=True)
class Forward:
    """Advance by *n* units along the working axis."""
    n: float = 1.0
    type: InstructionType = field(default=InstructionType.FWD, init=False)


@dataclass(frozen=True)
class Return:
    """Move back by *n* units (回帰)."""
    n: float = 1.0
    type: InstructionType = field(default=InstructionType.RET, init=False)


@dataclass(frozen=True)
class Cross:
    """Switch between surface and back (表裏反転).

    *angle* (degrees) controls the diagonal offset for zig-zag stitches
    or voice-crossing intervals.  *depth* (0.0-1.0) controls how far
    the needle penetrates (or how prominent the voice crossing is).
    *wrap* = True for edge-wrapping stitches (かがり縫い / ostinato).
    """
    angle: float = 0.0
    depth: float = 1.0
    wrap: bool = False
    type: InstructionType = field(default=InstructionType.CROSS, init=False)


@dataclass(frozen=True)
class Tension:
    """Set tension level (0.0 = slack/pp, 1.0 = taut/ff)."""
    value: float = 0.5
    type: InstructionType = field(default=InstructionType.TENSION, init=False)


@dataclass(frozen=True)
class Anchor:
    """Fix the current position (玉結び / tonic resolution)."""
    type: InstructionType = field(default=InstructionType.ANCHOR, init=False)


Instruction = Forward | Return | Cross | Tension | Anchor


# ---------------------------------------------------------------------------
# Card & Deck
# ---------------------------------------------------------------------------

@dataclass
class Card:
    """A named group of instructions — one Jacquard punch card."""
    name: str
    instructions: List[Instruction] = field(default_factory=list)
    repeat: int = 1
    loom_hint: str = ""    # human-readable description for sewing
    tone_hint: str = ""    # human-readable description for music

    # -- Music-specific metadata (optional) ---------------------------------
    chord_label: Optional[str] = None       # e.g. "Dm7", "G7", "Cmaj7"
    scale_degree: Optional[str] = None      # e.g. "ii", "V", "I"
    root_midi: Optional[int] = None         # MIDI note number for chord root
    chord_notes_midi: Optional[List[int]] = None  # all chord tones

    # -- Stitch-specific metadata (optional) --------------------------------
    stitch_type: Optional[str] = None       # e.g. "back_stitch", "running"


@dataclass
class Deck:
    """A sequence of Cards — the full Jacquard program."""
    title: str = "Untitled"
    description: str = ""
    cards: List[Card] = field(default_factory=list)
    bpm: int = 120              # tempo for MIDI rendering
    key_root: int = 60          # MIDI note of tonal centre (C4 = 60)
    stitch_unit_mm: float = 3.0 # physical size of 1 unit in mm

    def expanded_cards(self) -> List[Card]:
        """Yield each card repeated according to its *repeat* count."""
        result: List[Card] = []
        for card in self.cards:
            for _ in range(card.repeat):
                result.append(card)
        return result

    # -- Serialisation -------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialise to a plain dict (JSON-friendly)."""

        def _instr(inst: Instruction) -> dict:
            d = {"op": inst.type.name}
            if isinstance(inst, Forward):
                d["n"] = inst.n
            elif isinstance(inst, Return):
                d["n"] = inst.n
            elif isinstance(inst, Cross):
                d["angle"] = inst.angle
                d["depth"] = inst.depth
                d["wrap"] = inst.wrap
            elif isinstance(inst, Tension):
                d["value"] = inst.value
            return d

        def _card(c: Card) -> dict:
            cd: dict = {
                "name": c.name,
                "instructions": [_instr(i) for i in c.instructions],
                "repeat": c.repeat,
            }
            if c.loom_hint:
                cd["loom_hint"] = c.loom_hint
            if c.tone_hint:
                cd["tone_hint"] = c.tone_hint
            if c.chord_label:
                cd["chord_label"] = c.chord_label
            if c.scale_degree:
                cd["scale_degree"] = c.scale_degree
            if c.root_midi is not None:
                cd["root_midi"] = c.root_midi
            if c.chord_notes_midi:
                cd["chord_notes_midi"] = c.chord_notes_midi
            if c.stitch_type:
                cd["stitch_type"] = c.stitch_type
            return cd

        return {
            "title": self.title,
            "description": self.description,
            "bpm": self.bpm,
            "key_root": self.key_root,
            "stitch_unit_mm": self.stitch_unit_mm,
            "cards": [_card(c) for c in self.cards],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, d: dict) -> "Deck":
        op_map = {
            "FWD": lambda kw: Forward(**{k: v for k, v in kw.items() if k != "op"}),
            "RET": lambda kw: Return(**{k: v for k, v in kw.items() if k != "op"}),
            "CROSS": lambda kw: Cross(**{k: v for k, v in kw.items() if k != "op"}),
            "TENSION": lambda kw: Tension(**{k: v for k, v in kw.items() if k != "op"}),
            "ANCHOR": lambda kw: Anchor(),
        }
        cards: List[Card] = []
        for cd in d.get("cards", []):
            instructions = []
            for raw in cd.get("instructions", []):
                op = raw["op"]
                instructions.append(op_map[op](raw))
            card = Card(
                name=cd["name"],
                instructions=instructions,
                repeat=cd.get("repeat", 1),
                loom_hint=cd.get("loom_hint", ""),
                tone_hint=cd.get("tone_hint", ""),
                chord_label=cd.get("chord_label"),
                scale_degree=cd.get("scale_degree"),
                root_midi=cd.get("root_midi"),
                chord_notes_midi=cd.get("chord_notes_midi"),
                stitch_type=cd.get("stitch_type"),
            )
            cards.append(card)
        return cls(
            title=d.get("title", "Untitled"),
            description=d.get("description", ""),
            cards=cards,
            bpm=d.get("bpm", 120),
            key_root=d.get("key_root", 60),
            stitch_unit_mm=d.get("stitch_unit_mm", 3.0),
        )

    @classmethod
    def from_json(cls, text: str) -> "Deck":
        return cls.from_dict(json.loads(text))
