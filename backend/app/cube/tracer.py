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
    buffer_cubie = S.CUBIE_OF[buffer_fid]
    buffer_stickers = S.CUBIE_STICKERS[buffer_cubie]

    def buffer_solved() -> bool:
        return all(w[f] == f for f in buffer_stickers)

    def first_unsolved_other() -> int | None:
        for p in ordered_facelets:
            if S.CUBIE_OF[p] != buffer_cubie and w[p] != p:
                return p
        return None

    max_steps = len(ordered_facelets) * 3 + 20
    for _ in range(max_steps + 1):
        if buffer_solved():
            target = first_unsolved_other()
            if target is None:
                return targets  # orbit solved
        else:
            shown = w[buffer_fid]
            if S.CUBIE_OF[shown] == buffer_cubie:
                # Buffer piece is home but twisted -> break out to resolve it.
                target = first_unsolved_other()
                if target is None:
                    return targets
            else:
                target = shown  # home of the sticker shown in the buffer
        targets.append(letter_by_facelet[target])
        S.piece_swap(w, buffer_fid, target)

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
