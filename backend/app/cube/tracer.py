"""Tracer — turn a scrambled state into a Speffz memo (letter sequences).

The tracer is a buffer-swap solving *simulation*: starting from the buffer
sticker, repeatedly send the sticker currently in the buffer to its home
(recording that home's letter), swapping it in. When the buffer is solved but
pieces remain, "break" into the lowest-letter unsolved sticker and continue.

Because ``validator.solves`` replays the identical swap semantics, a memo
produced here is guaranteed to validate as solved. Cycle breaks, an
already-solved buffer, and in-place flips/twists all emerge naturally from the
sticker-permutation model (a twist/flip simply leaves multiple stickers of one
piece unsolved).
"""
from __future__ import annotations

from dataclasses import dataclass

from . import scheme as SC
from . import state as S

# Defaults: corner buffer UFR (U sticker = "C"), edge buffer UF (U sticker = "C").
DEFAULT_CORNER_BUFFER = "C"
DEFAULT_EDGE_BUFFER = "C"


@dataclass
class Memo:
    corners: list[str]
    edges: list[str]
    corner_buffer: str
    edge_buffer: str
    parity: bool  # odd piece permutation — needs a parity fix in 3-cycle methods

    @property
    def has_parity(self) -> bool:
        return self.parity


def _trace_orbit(state: tuple[int, ...], ordered_facelets: list[int],
                 buffer_fid: int, letter_by_facelet: dict[int, str]) -> list[str]:
    w = list(state)
    targets: list[str] = []
    max_steps = len(ordered_facelets) * 3 + 10

    def first_unsolved() -> int | None:
        for p in ordered_facelets:
            if p != buffer_fid and w[p] != p:
                return p
        return None

    for _ in range(max_steps + 1):
        if w[buffer_fid] == buffer_fid:
            target = first_unsolved()
            if target is None:
                return targets  # orbit solved
        else:
            target = w[buffer_fid]
        targets.append(letter_by_facelet[target])
        w[buffer_fid], w[target] = w[target], w[buffer_fid]

    raise RuntimeError("tracer did not converge")  # pragma: no cover


def trace(state: tuple[int, ...],
          corner_buffer: str = DEFAULT_CORNER_BUFFER,
          edge_buffer: str = DEFAULT_EDGE_BUFFER) -> Memo:
    corners = _trace_orbit(
        state, SC.CORNER_FACELETS_IN_LETTER_ORDER,
        SC.CORNER_FACELET_BY_LETTER[corner_buffer], SC.CORNER_LETTER_BY_FACELET,
    )
    edges = _trace_orbit(
        state, SC.EDGE_FACELETS_IN_LETTER_ORDER,
        SC.EDGE_FACELET_BY_LETTER[edge_buffer], SC.EDGE_LETTER_BY_FACELET,
    )
    # True BLD parity = odd *piece* permutation (corners and edges always agree).
    parity = S.permutation_parity(S.corner_permutation(state)) == 1
    return Memo(corners=corners, edges=edges, parity=parity,
                corner_buffer=corner_buffer, edge_buffer=edge_buffer)
