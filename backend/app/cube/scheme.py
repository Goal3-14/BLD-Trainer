"""Speffz lettering scheme.

Maps the 24 corner facelets and 24 edge facelets to letters A-X, following the
community-standard Speffz layout: white top / green front, face order
U, L, F, R, B, D, lettered clockwise from each face's top-left, with the D face
lettered as if after an x2 rotation. (These rules are confirmed by the
speedsolving.com Speffz reference; the explicit table below is derived from
them and anchored to the verified cube geometry in ``state.py``.)

Corner and edge letters are independent label spaces — letter "A" names a
corner sticker and, separately, an edge sticker.
"""
from __future__ import annotations

from . import state as S

_DIR: dict[str, S.Vec] = {
    "U": (0, 1, 0),
    "D": (0, -1, 0),
    "F": (0, 0, 1),
    "B": (0, 0, -1),
    "R": (1, 0, 0),
    "L": (-1, 0, 0),
}

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWX"

# Each entry is (sticker_face, cubie), in Speffz A..X order.
# sticker_face is the face the sticker shows; cubie is the piece it belongs to.
_CORNER_SPEFFZ: list[tuple[str, str]] = [
    ("U", "UBL"), ("U", "UBR"), ("U", "UFR"), ("U", "UFL"),  # A-D  (U face)
    ("L", "UBL"), ("L", "UFL"), ("L", "DFL"), ("L", "DBL"),  # E-H  (L face)
    ("F", "UFL"), ("F", "UFR"), ("F", "DFR"), ("F", "DFL"),  # I-L  (F face)
    ("R", "UFR"), ("R", "UBR"), ("R", "DBR"), ("R", "DFR"),  # M-P  (R face)
    ("B", "UBR"), ("B", "UBL"), ("B", "DBL"), ("B", "DBR"),  # Q-T  (B face)
    ("D", "DFL"), ("D", "DFR"), ("D", "DBR"), ("D", "DBL"),  # U-X  (D face)
]
_EDGE_SPEFFZ: list[tuple[str, str]] = [
    ("U", "UB"), ("U", "UR"), ("U", "UF"), ("U", "UL"),  # A-D  (U face)
    ("L", "UL"), ("L", "FL"), ("L", "DL"), ("L", "BL"),  # E-H  (L face)
    ("F", "UF"), ("F", "FR"), ("F", "DF"), ("F", "FL"),  # I-L  (F face)
    ("R", "UR"), ("R", "BR"), ("R", "DR"), ("R", "FR"),  # M-P  (R face)
    ("B", "UB"), ("B", "BL"), ("B", "DB"), ("B", "BR"),  # Q-T  (B face)
    ("D", "DF"), ("D", "DR"), ("D", "DB"), ("D", "DL"),  # U-X  (D face)
]


def _spec_to_facelet(sticker_face: str, cubie: str) -> int:
    pos: S.Vec = (
        sum(_DIR[c][0] for c in cubie),
        sum(_DIR[c][1] for c in cubie),
        sum(_DIR[c][2] for c in cubie),
    )
    return S.facelet_id(pos, _DIR[sticker_face])


CORNER_FACELET_BY_LETTER: dict[str, int] = {
    LETTERS[i]: _spec_to_facelet(*spec) for i, spec in enumerate(_CORNER_SPEFFZ)
}
EDGE_FACELET_BY_LETTER: dict[str, int] = {
    LETTERS[i]: _spec_to_facelet(*spec) for i, spec in enumerate(_EDGE_SPEFFZ)
}
CORNER_LETTER_BY_FACELET: dict[int, str] = {v: k for k, v in CORNER_FACELET_BY_LETTER.items()}
EDGE_LETTER_BY_FACELET: dict[int, str] = {v: k for k, v in EDGE_FACELET_BY_LETTER.items()}

# Orbit facelets in Speffz letter order (A..X) — used for deterministic cycle breaks.
CORNER_FACELETS_IN_LETTER_ORDER: list[int] = [CORNER_FACELET_BY_LETTER[c] for c in LETTERS]
EDGE_FACELETS_IN_LETTER_ORDER: list[int] = [EDGE_FACELET_BY_LETTER[c] for c in LETTERS]


def _piece_name(pos: S.Vec) -> str:
    """Human piece name from a cubie position, e.g. (1,1,1) -> 'UFR'."""
    name = ""
    if pos[1] > 0:
        name += "U"
    elif pos[1] < 0:
        name += "D"
    if pos[2] > 0:
        name += "F"
    elif pos[2] < 0:
        name += "B"
    if pos[0] > 0:
        name += "R"
    elif pos[0] < 0:
        name += "L"
    return name


def _labels(facelet_by_letter: dict[str, int]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for letter in LETTERS:
        fl = S.FACELETS[facelet_by_letter[letter]]
        out.append({
            "letter": letter,
            "piece": _piece_name(fl.pos),
            "sticker": S.NORMAL_TO_FACE[fl.normal],
        })
    return out


def corner_labels() -> list[dict[str, str]]:
    return _labels(CORNER_FACELET_BY_LETTER)


def edge_labels() -> list[dict[str, str]]:
    return _labels(EDGE_FACELET_BY_LETTER)
