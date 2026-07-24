"""
MIDI Tone Renderer (Music-Box Renderer).

Interprets an SITS9 Deck as a MIDI file.

Mapping logic
─────────────
Each Card is rendered as a beat-aligned musical event:

  FWD(n)      → note duration proportional to n
  RET(n)      → rest (silence) proportional to n, representing the
                "return" motion; optionally a grace-note descent
  CROSS       → voice change: toggle between melody (ch 0) and
                bass/counterpoint (ch 1)
  TENSION(v)  → MIDI velocity (v * 127)
  ANCHOR      → play the tonic chord (root + 3rd + 5th) as a
                sustained resolution

If a Card carries *chord_notes_midi*, those notes are played directly.
Otherwise, the renderer uses the Deck's *key_root* offset by the
FWD/RET accumulated position to choose pitches.
"""

from __future__ import annotations

import re
from pathlib import Path

import mido

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


class MidiRenderer:
    """Render an SITS9 Deck to a Standard MIDI file."""

    def __init__(
        self,
        ticks_per_beat: int = 480,
        default_velocity: int = 80,
        sustain_ticks: int | None = None,
    ):
        self.ticks_per_beat = ticks_per_beat
        self.default_velocity = default_velocity
        self.sustain_ticks = sustain_ticks  # None → derive from FWD

    def render(self, deck: Deck, output_path: str | Path) -> Path:
        output_path = Path(output_path)
        mid = mido.MidiFile(ticks_per_beat=self.ticks_per_beat)

        # Track 0: tempo + metadata
        meta_track = mido.MidiTrack()
        mid.tracks.append(meta_track)
        meta_track.append(
            mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(deck.bpm))
        )
        meta_track.append(
            mido.MetaMessage("track_name", name=_ascii(deck.title))
        )

        # Track 1: melody / main voice (channel 0)
        melody_track = mido.MidiTrack()
        mid.tracks.append(melody_track)
        melody_track.append(
            mido.MetaMessage("track_name", name="Melody (surface)")
        )
        # Piano on ch0
        melody_track.append(mido.Message("program_change", program=0, channel=0))

        # Track 2: bass / counter voice (channel 1)
        bass_track = mido.MidiTrack()
        mid.tracks.append(bass_track)
        bass_track.append(
            mido.MetaMessage("track_name", name="Bass (back)")
        )
        # Strings on ch1
        bass_track.append(mido.Message("program_change", program=48, channel=1))

        # -- simulation state --
        velocity = self.default_velocity
        on_surface = True  # True → melody track, False → bass track
        position = 0.0     # accumulated FWD/RET
        melody_time = 0    # delta accumulator for melody track
        bass_time = 0      # delta accumulator for bass track

        for card in deck.expanded_cards():
            # Add card-name marker
            active_track = melody_track if on_surface else bass_track
            active_track.append(
                mido.MetaMessage("marker", text=_ascii(card.name), time=0)
            )

            for inst in card.instructions:
                if isinstance(inst, Forward):
                    dur = int(inst.n * self.ticks_per_beat)
                    notes = self._resolve_notes(card, deck, position)
                    ch = 0 if on_surface else 1
                    track = melody_track if on_surface else bass_track
                    acc = melody_time if on_surface else bass_time

                    if notes:
                        # note-on for all chord tones
                        for i, note in enumerate(notes):
                            track.append(
                                mido.Message(
                                    "note_on",
                                    note=note,
                                    velocity=velocity,
                                    channel=ch,
                                    time=acc if i == 0 else 0,
                                )
                            )
                        # note-off after duration
                        for i, note in enumerate(notes):
                            track.append(
                                mido.Message(
                                    "note_off",
                                    note=note,
                                    velocity=0,
                                    channel=ch,
                                    time=dur if i == 0 else 0,
                                )
                            )
                        if on_surface:
                            melody_time = 0
                            bass_time += dur
                        else:
                            bass_time = 0
                            melody_time += dur
                    else:
                        # no notes → rest
                        if on_surface:
                            melody_time += dur
                        else:
                            bass_time += dur

                    position += inst.n

                elif isinstance(inst, Return):
                    dur = int(inst.n * self.ticks_per_beat * 0.5)
                    melody_time += dur
                    bass_time += dur
                    position -= inst.n

                elif isinstance(inst, Cross):
                    on_surface = not on_surface

                elif isinstance(inst, Tension):
                    velocity = max(1, min(127, int(inst.value * 127)))

                elif isinstance(inst, Anchor):
                    # Play the tonic as a whole-note chord
                    root = deck.key_root
                    chord = [root, root + 4, root + 7]  # major triad
                    dur = self.ticks_per_beat * 2
                    ch = 0 if on_surface else 1
                    track = melody_track if on_surface else bass_track
                    acc = melody_time if on_surface else bass_time

                    for i, note in enumerate(chord):
                        track.append(
                            mido.Message(
                                "note_on",
                                note=note,
                                velocity=velocity,
                                channel=ch,
                                time=acc if i == 0 else 0,
                            )
                        )
                    for i, note in enumerate(chord):
                        track.append(
                            mido.Message(
                                "note_off",
                                note=note,
                                velocity=0,
                                channel=ch,
                                time=dur if i == 0 else 0,
                            )
                        )
                    if on_surface:
                        melody_time = 0
                        bass_time += dur
                    else:
                        bass_time = 0
                        melody_time += dur

        mid.save(str(output_path))
        return output_path

    # -- helpers -------------------------------------------------------------

    @staticmethod
    def _resolve_notes(
        card: Card, deck: Deck, position: float
    ) -> list[int]:
        """Pick MIDI notes for a card, preferring explicit chord data."""
        if card.chord_notes_midi:
            return list(card.chord_notes_midi)
        if card.root_midi is not None:
            root = card.root_midi
            return [root, root + 4, root + 7]
        # Fallback: derive from key_root + position
        note = deck.key_root + int(position) % 12
        return [note]


def _ascii(text: str) -> str:
    """Strip non-Latin-1 chars for MIDI meta messages."""
    return re.sub(r'[^\x00-\xff]', '', text)
