"""Tracer — turn a scrambled state into a Speffz memo (letter sequences).

A BLD "shot" places a whole *piece*: from the buffer sticker, send the piece
currently in the buffer to the home of the sticker it shows (recording that
home's letter) via a piece swap, which moves all of the piece's stickers
together with the correct orientation. When the buffer piece is solved (or
stuck twisted in place) but pieces remain, break into the lowest-letter
unsolved piece on another cubie.

``validator.validate`` replays the identical piece swaps, so a memo produced
here validates as solved by construction. One shot per piece keeps memos at
realistic lengths (corners ~8-11, edges ~11-13), and orientation (twists/flips)
is handled because the piece carries its stickers with it.

The same routine traces every orbit of every cube size: corners and edges on
3x3, plus wings and centres on 4x4, plus midges and edge centres on 5x5. Two
things differ on the big cubes, both handled here:

* solved is judged by colour per cubie, so a 4x4's identical wings or centres
  count as solved when swapped with each other — because they look it;
* a centre shot has four equally valid destinations, so the target is chosen
  (lowest unsolved slot of the right colour) rather than read off the sticker.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import scheme as SC
from . import state as S

# Defaults: corner buffer UFR (U sticker = "C"), edge buffer UF (U sticker = "C").
DEFAULT_CORNER_BUFFER = "C"
DEFAULT_EDGE_BUFFER = "C"


@dataclass
class Memo:
    """A full memo. ``targets`` keys are orbit kinds; ``corners``/``edges`` are
    kept as the 3x3 view onto the same data."""
    targets: dict[str, list[str]] = field(default_factory=dict)
    buffers: dict[str, str] = field(default_factory=dict)
    parity: bool = False  # odd corner permutation

    @property
    def corners(self) -> list[str]:
        return self.targets.get("corner", [])

    @property
    def edges(self) -> list[str]:
        return self.targets.get("edge", [])

    @property
    def corner_buffer(self) -> str:
        return self.buffers.get("corner", DEFAULT_CORNER_BUFFER)

    @property
    def edge_buffer(self) -> str:
        return self.buffers.get("edge", DEFAULT_EDGE_BUFFER)

    @property
    def has_parity(self) -> bool:
        return self.parity

    def orbit_parity(self, kind: str) -> bool:
        """Odd number of targets means an odd permutation of that orbit: every
        shot is a transposition, so the count *is* the parity."""
        return len(self.targets.get(kind, [])) % 2 == 1


def _trace_orbit(state: tuple[int, ...], orbit: SC.Orbit, buffer_letter: str,
                 cube: S.CubeModel) -> list[str]:
    w = list(state)
    ordered = orbit.facelets_in_letter_order
    buffer_fid = orbit.facelet_by_letter[buffer_letter]
    targets: list[str] = []
    buffer_cubie = cube.cubie_of[buffer_fid]

    def solved(fid: int) -> bool:
        return cube.cubie_solved(w, cube.cubie_of[fid])

    def first_unsolved_other() -> int | None:
        # Where pieces are interchangeable, a cycle break into a slot holding
        # the same colour the buffer holds would swap two identical stickers
        # and change nothing — the trace would spin there forever. Such a
        # target always exists while the orbit is unsolved, by counting: the
        # four stickers of a colour cannot all sit outside their own slots
        # while every one of those slots is already solved.
        held = cube.facelets[w[buffer_fid]].color if orbit.interchangeable else None
        for p in ordered:
            if cube.cubie_of[p] == buffer_cubie or solved(p):
                continue
            if held is not None and cube.facelets[w[p]].color == held:
                continue
            return p
        return None

    def choose_center_target(shown: int) -> int | None:
        """Any unsolved slot whose home colour matches the sticker held."""
        color = cube.facelets[shown].color
        for p in ordered:
            if (cube.cubie_of[p] != buffer_cubie
                    and cube.facelets[p].color == color
                    and not solved(p)):
                return p
        return None

    max_steps = len(ordered) * 3 + 20
    for _ in range(max_steps + 1):
        if solved(buffer_fid):
            target = first_unsolved_other()
            if target is None:
                return targets  # orbit solved
        else:
            shown = w[buffer_fid]
            if orbit.interchangeable:
                target = choose_center_target(shown)
                if target is None:
                    target = first_unsolved_other()
                    if target is None:
                        return targets
            elif cube.cubie_of[shown] == buffer_cubie:
                # Buffer piece is home but twisted -> break out to resolve it.
                target = first_unsolved_other()
                if target is None:
                    return targets
            else:
                target = shown  # home of the sticker shown in the buffer
        targets.append(orbit.letter_by_facelet[target])
        cube.piece_swap(w, buffer_fid, target)

    raise RuntimeError("tracer did not converge")  # pragma: no cover


def trace_cube(state: tuple[int, ...], n: int = 3,
               buffers: dict[str, str] | None = None) -> Memo:
    """Trace every lettered orbit of an n x n cube."""
    cube = S.model(n)
    orbits = SC.ORBITS[n]
    chosen = {kind: o.default_buffer for kind, o in orbits.items()}
    for kind, letter in (buffers or {}).items():
        if kind in chosen:
            chosen[kind] = letter
    targets = {
        kind: _trace_orbit(state, orbit, chosen[kind], cube)
        for kind, orbit in orbits.items()
    }
    return Memo(targets=targets, buffers=chosen,
                parity=len(targets.get("corner", [])) % 2 == 1)


def trace(state: tuple[int, ...],
          corner_buffer: str = DEFAULT_CORNER_BUFFER,
          edge_buffer: str = DEFAULT_EDGE_BUFFER) -> Memo:
    """3x3 tracing, unchanged."""
    return trace_cube(state, 3, {"corner": corner_buffer, "edge": edge_buffer})
