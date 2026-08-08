"""Validator — does a memo (letter sequence) actually solve the scramble?

Validation is by *simulation*, not by string-matching against one "correct"
answer: there is no single correct memo (it depends on buffer, cycle-break
choices, and parity handling). We replay the memo as piece swaps (the same
elementary shot the tracer uses) on the scrambled state and check whether the
cube ends solved. This works for any buffer/scheme and any valid tracing.

That choice pays for itself on the big cubes, where a centre shot has four
equally valid destinations: no table of "the" right memo could ever have been
written, but replaying the solver's own targets still answers the question.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import scheme as SC
from . import state as S
from .tracer import DEFAULT_CORNER_BUFFER, DEFAULT_EDGE_BUFFER


@dataclass
class Verdict:
    solved: bool
    by_orbit: dict[str, bool] = field(default_factory=dict)

    @property
    def corners_solved(self) -> bool:
        return self.by_orbit.get("corner", True)

    @property
    def edges_solved(self) -> bool:
        return self.by_orbit.get("edge", True)


def _apply_shots(w: list[int], buffer_fid: int, targets: list[str],
                 facelet_by_letter: dict[str, int], cube: S.CubeModel) -> None:
    for letter in targets:
        cube.piece_swap(w, buffer_fid, facelet_by_letter[letter])


def validate_cube(state: tuple[int, ...], targets: dict[str, list[str]], n: int = 3,
                  buffers: dict[str, str] | None = None) -> Verdict:
    """Replay a memo orbit by orbit and report which orbits ended solved."""
    cube = S.model(n)
    orbits = SC.ORBITS[n]
    w = list(state)
    for kind, orbit in orbits.items():
        letter = (buffers or {}).get(kind) or orbit.default_buffer
        _apply_shots(w, orbit.facelet_by_letter[letter], targets.get(kind, []),
                     orbit.facelet_by_letter, cube)
    by_orbit = {kind: cube.orbit_solved(w, kind) for kind in orbits}
    return Verdict(solved=all(by_orbit.values()), by_orbit=by_orbit)


def validate(state: tuple[int, ...], corner_targets: list[str], edge_targets: list[str],
             corner_buffer: str = DEFAULT_CORNER_BUFFER,
             edge_buffer: str = DEFAULT_EDGE_BUFFER) -> Verdict:
    """3x3 validation, unchanged."""
    return validate_cube(
        state, {"corner": corner_targets, "edge": edge_targets}, 3,
        {"corner": corner_buffer, "edge": edge_buffer},
    )


def solves(state: tuple[int, ...], corner_targets: list[str], edge_targets: list[str],
           corner_buffer: str = DEFAULT_CORNER_BUFFER,
           edge_buffer: str = DEFAULT_EDGE_BUFFER) -> bool:
    return validate(state, corner_targets, edge_targets, corner_buffer, edge_buffer).solved
