"""Random-move scramble generation for 3x3, 4x4 and 5x5.

Produces face moves and, on the big cubes, two-layer wide moves (Rw, Lw', Uw2).
Inner layers are only ever turned as part of a wide move: there is no slice-only
token in the move set, and consecutive turns of the same face are rejected, so a
pair like ``R Rw'`` — which would net to a bare inner-slice turn — cannot appear
either.

Redundancy filtering is the usual kind: no two consecutive turns of the same
face, and no same-axis "sandwich" (e.g. R L R). Fine for practice; WCA
random-state scrambles can replace it later.
"""
from __future__ import annotations

import random

from . import state as S

FACES = "URFDLB"
_AXIS = {"U": "y", "D": "y", "R": "x", "L": "x", "F": "z", "B": "z"}
_MODIFIERS = ["", "'", "2"]

# Roughly WCA lengths: enough turns that no orbit is left near-solved.
DEFAULT_LENGTH = {3: 20, 4: 40, 5: 60}


def _widths(n: int) -> tuple[str, ...]:
    return ("",) if n == 3 else ("", "w")


def generate_scramble(length: int | None = None, seed: int | None = None,
                      prefix: list[str] | None = None, n: int = 3) -> list[str]:
    """Return `length` new move tokens (e.g. ["R", "Uw'", "F2", ...]).

    `prefix` is a sequence the new moves will be appended to (i.e. moves already
    applied to the cube). It is not included in the result, but its trailing
    faces seed the redundancy filter so the join is clean — no repeated face and
    no three-on-an-axis across the seam.
    """
    if length is None:
        length = DEFAULT_LENGTH[n]
    widths = _widths(n)
    rng = random.Random(seed)
    moves: list[str] = []
    # Whole tokens, not just faces: the wide-move rule below needs to know how
    # thick the previous turn was, and it has to hold across a prefix seam too.
    history: list[str] = list(prefix or [])

    def face_of(tok: str) -> str:
        return tok[0]

    while len(moves) < length:
        face = rng.choice(FACES)
        width = rng.choice(widths)
        if history and face_of(history[-1]) == face:
            continue  # no immediate repeat of the same face, at any width
        if (len(history) >= 2
                and _AXIS[face] == _AXIS[face_of(history[-1])] == _AXIS[face_of(history[-2])]):
            continue  # no three consecutive moves on the same axis
        # No wide move straight after a wide move on the opposite face: `Uw Dw'`
        # means regripping the whole cube twice over, which is miserable to
        # execute. The same face is already excluded, so a shared axis here can
        # only mean the opposite face.
        if (width == "w" and history and "w" in history[-1]
                and _AXIS[face_of(history[-1])] == _AXIS[face]):
            continue
        tok = face + width + rng.choice(_MODIFIERS)
        history.append(tok)
        moves.append(tok)
    return moves


def is_valid(moves: list[str], n: int = 3) -> bool:
    return all(m in S.model(n).MOVES for m in moves)
