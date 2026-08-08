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


def _spec_to_facelet(sticker_face: str, cubie: str, cube: S.CubeModel = S.CUBE3) -> int:
    """Corner or edge sticker. A cubie name like "UFR" gives unit steps; layers
    live at +/- outer, so scale onto the model's grid. Normals stay unit."""
    pos: S.Vec = tuple(  # type: ignore[assignment]
        cube.outer * sum(_DIR[c][i] for c in cubie) for i in range(3)
    )
    return cube.facelet_id(pos, _DIR[sticker_face])


# --- Big-cube orbits, derived from the two Speffz tables ----------------------
#
# Wings, x-centres and t-centres are not lettered by hand. Each is derived from
# the corner or edge table it sits beside, so a mis-typed table cannot put a
# letter in the wrong place on one size only.


def _other_faces(cubie: str, sticker_face: str) -> list[str]:
    return [c for c in cubie if c != sticker_face]


def _clockwise_from(sticker_face: str, direction: S.Vec) -> S.Vec:
    """Where a clockwise turn of ``sticker_face`` sends ``direction`` — i.e. the
    next slot round that face, which is the wing chirality rule."""
    axis, quarter = S.clockwise_quarter(sticker_face)
    return S.rotate(direction, axis, quarter)


def _wing_facelet(sticker_face: str, cubie: str, cube: S.CubeModel) -> int:
    """Of the two wings at this edge slot, the one displaced clockwise."""
    inner = cube.outer - 2
    other = _other_faces(cubie, sticker_face)[0]
    cw = _clockwise_from(sticker_face, _DIR[other])
    pos: S.Vec = tuple(  # type: ignore[assignment]
        cube.outer * (_DIR[sticker_face][i] + _DIR[other][i]) + inner * cw[i]
        for i in range(3)
    )
    return cube.facelet_id(pos, _DIR[sticker_face])


def _xcenter_facelet(sticker_face: str, cubie: str, cube: S.CubeModel) -> int:
    """The centre tucked into this corner, e.g. corner letter A -> the U centre
    nearest UBL."""
    inner = cube.outer - 2
    others = _other_faces(cubie, sticker_face)
    pos: S.Vec = tuple(  # type: ignore[assignment]
        cube.outer * _DIR[sticker_face][i] + inner * sum(_DIR[o][i] for o in others)
        for i in range(3)
    )
    return cube.facelet_id(pos, _DIR[sticker_face])


def _tcenter_facelet(sticker_face: str, cubie: str, cube: S.CubeModel) -> int:
    """The centre beside this edge, e.g. edge letter D -> the U centre by UL."""
    inner = cube.outer - 2
    other = _other_faces(cubie, sticker_face)[0]
    pos: S.Vec = tuple(  # type: ignore[assignment]
        cube.outer * _DIR[sticker_face][i] + inner * _DIR[other][i] for i in range(3)
    )
    return cube.facelet_id(pos, _DIR[sticker_face])


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


# --- Orbits per cube size ----------------------------------------------------

# Which Speffz table each orbit hangs off, and how to place its sticker.
_BUILDERS: dict[str, tuple[list[tuple[str, str]], object]] = {
    "corner": (_CORNER_SPEFFZ, _spec_to_facelet),
    "edge": (_EDGE_SPEFFZ, _spec_to_facelet),
    "wing": (_EDGE_SPEFFZ, _wing_facelet),
    "xcenter": (_CORNER_SPEFFZ, _xcenter_facelet),
    "tcenter": (_EDGE_SPEFFZ, _tcenter_facelet),
}

# Buffers are data, per size: a 3BLD edge buffer is UF/C, but a 5BLD midge
# buffer is conventionally DF/U.
DEFAULT_BUFFERS: dict[int, dict[str, str]] = {
    3: {"corner": "C", "edge": "C"},
    4: {"corner": "C", "wing": "U", "xcenter": "A"},
    5: {"corner": "C", "edge": "U", "wing": "U", "xcenter": "A", "tcenter": "D"},
}


def _title(kind: str, n: int) -> str:
    if kind == "edge":
        return "Edges" if n == 3 else "Midges"
    return {"corner": "Corners", "wing": "Wings",
            "xcenter": "Centres", "tcenter": "Edge centres"}[kind]


class Orbit:
    """One lettered piece class on one cube size."""

    def __init__(self, kind: str, n: int, cube: S.CubeModel) -> None:
        table, place = _BUILDERS[kind]
        self.kind = kind
        self.title = _title(kind, n)
        self.facelet_by_letter: dict[str, int] = {
            LETTERS[i]: place(face, cubie, cube)  # type: ignore[operator]
            for i, (face, cubie) in enumerate(table)
        }
        self.letter_by_facelet: dict[int, str] = {
            v: k for k, v in self.facelet_by_letter.items()
        }
        self.facelets_in_letter_order: list[int] = [
            self.facelet_by_letter[c] for c in LETTERS
        ]
        self.default_buffer = DEFAULT_BUFFERS[n][kind]
        # Centres come in fours of a colour, so a shot may go to any unsolved
        # slot of the colour shown — the target is a choice, not a lookup.
        self.interchangeable = kind in ("xcenter", "tcenter")

    def labels(self, cube: S.CubeModel) -> list[dict[str, str]]:
        out: list[dict[str, str]] = []
        for letter in LETTERS:
            fl = cube.facelets[self.facelet_by_letter[letter]]
            out.append({
                "letter": letter,
                "piece": _piece_name(fl.pos),
                "sticker": S.NORMAL_TO_FACE[fl.normal],
            })
        return out


def orbits_for(n: int) -> dict[str, Orbit]:
    """Lettered orbits of an n x n cube, in engine order. Which orbits exist is
    read off the model, so it stays in step with the geometry."""
    cube = S.model(n)
    return {
        kind: Orbit(kind, n, cube)
        for kind in S.KIND_ORDER
        if cube.ids_by_kind[kind]
    }


ORBITS: dict[int, dict[str, Orbit]] = {n: orbits_for(n) for n in (3, 4, 5)}
