"""Validator — does a memo (letter sequence) actually solve the scramble?

Validation is by *simulation*, not by string-matching against one "correct"
answer: there is no single correct memo (it depends on buffer, cycle-break
choices, and parity handling). We replay the memo as buffer-swaps on the
scrambled state and check whether the cube ends solved. This works for any
buffer/scheme and any valid tracing.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import scheme as SC
from . import state as S
from .tracer import DEFAULT_CORNER_BUFFER, DEFAULT_EDGE_BUFFER


@dataclass
class Verdict:
    solved: bool
    corners_solved: bool
    edges_solved: bool


def _apply_swaps(w: list[int], buffer_fid: int, targets: list[str],
                 facelet_by_letter: dict[str, int]) -> None:
    for letter in targets:
        t = facelet_by_letter[letter]
        w[buffer_fid], w[t] = w[t], w[buffer_fid]


def _orbit_solved(w: list[int], orbit_ids: list[int]) -> bool:
    return all(w[p] == p for p in orbit_ids)


def validate(state: tuple[int, ...], corner_targets: list[str], edge_targets: list[str],
             corner_buffer: str = DEFAULT_CORNER_BUFFER,
             edge_buffer: str = DEFAULT_EDGE_BUFFER) -> Verdict:
    w = list(state)
    _apply_swaps(w, SC.CORNER_FACELET_BY_LETTER[corner_buffer],
                 corner_targets, SC.CORNER_FACELET_BY_LETTER)
    _apply_swaps(w, SC.EDGE_FACELET_BY_LETTER[edge_buffer],
                 edge_targets, SC.EDGE_FACELET_BY_LETTER)
    corners_ok = _orbit_solved(w, S.CORNER_IDS)
    edges_ok = _orbit_solved(w, S.EDGE_IDS)
    return Verdict(solved=corners_ok and edges_ok,
                   corners_solved=corners_ok, edges_solved=edges_ok)


def solves(state: tuple[int, ...], corner_targets: list[str], edge_targets: list[str],
           corner_buffer: str = DEFAULT_CORNER_BUFFER,
           edge_buffer: str = DEFAULT_EDGE_BUFFER) -> bool:
    return validate(state, corner_targets, edge_targets, corner_buffer, edge_buffer).solved
