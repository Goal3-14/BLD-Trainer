"""Random-move scramble generation for the 3x3 cube.

Produces a sequence of face moves with the usual redundancy filtering: no two
consecutive turns of the same face, and no same-axis "sandwich" (e.g. R L R).
This is fine for practice; WCA random-state scrambles can replace it later.
"""
from __future__ import annotations

import random

FACES = "URFDLB"
_AXIS = {"U": "y", "D": "y", "R": "x", "L": "x", "F": "z", "B": "z"}
_MODIFIERS = ["", "'", "2"]


def generate_scramble(
    length: int = 20, seed: int | None = None, prefix: list[str] | None = None
) -> list[str]:
    """Return `length` new move tokens (e.g. ["R", "U'", "F2", ...]).

    `prefix` is a sequence the new moves will be appended to (i.e. moves already
    applied to the cube). It is not included in the result, but its trailing
    faces seed the redundancy filter so the join is clean — no repeated face and
    no three-on-an-axis across the seam.
    """
    rng = random.Random(seed)
    moves: list[str] = []
    faces: list[str] = [tok[0] for tok in (prefix or [])]
    while len(moves) < length:
        face = rng.choice(FACES)
        if faces and face == faces[-1]:
            continue  # no immediate repeat of the same face
        if len(faces) >= 2 and _AXIS[face] == _AXIS[faces[-1]] == _AXIS[faces[-2]]:
            continue  # no three consecutive moves on the same axis
        faces.append(face)
        moves.append(face + rng.choice(_MODIFIERS))
    return moves
