"""Render a cube state as colors on the standard unfolded net.

The backend owns this (cube logic stays server-side): each face becomes a
row-major list of 9 color names that the frontend draws directly. Centers are
fixed per face; the 8 movable stickers come from the state.

Orientation: the lettering/positions are fixed, but which *color* sits on each
face is configurable (top color + front color). ``face_colors`` derives the
full face->color map for any valid orientation; the default white-top/green-
front reproduces the standard scheme.

Net layout (unfolded cross):

            U
          L F R B
            D
"""
from __future__ import annotations

from . import state as S

_RIGHT: dict[str, S.Vec] = {
    "U": (1, 0, 0), "L": (0, 0, 1), "F": (1, 0, 0),
    "R": (0, 0, -1), "B": (-1, 0, 0), "D": (1, 0, 0),
}
_DOWN: dict[str, S.Vec] = {
    "U": (0, 0, 1), "L": (0, -1, 0), "F": (0, -1, 0),
    "R": (0, -1, 0), "B": (0, -1, 0), "D": (0, 0, -1),
}

FACE_NET_ORDER = ["U", "L", "F", "R", "B", "D"]

COLORS = ["white", "yellow", "green", "blue", "red", "orange"]

# Color vectors in the standard solved orientation (white top, green front).
_COLOR_VEC: dict[str, S.Vec] = {
    "white": (0, 1, 0), "yellow": (0, -1, 0),
    "green": (0, 0, 1), "blue": (0, 0, -1),
    "red": (1, 0, 0), "orange": (-1, 0, 0),
}
OPPOSITE: dict[str, str] = {
    "white": "yellow", "yellow": "white",
    "green": "blue", "blue": "green",
    "red": "orange", "orange": "red",
}


def _dot(a: S.Vec, b: S.Vec) -> int:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: S.Vec, b: S.Vec) -> S.Vec:
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def face_colors(top: str = "white", front: str = "green") -> dict[str, str]:
    """Map each face (U/D/F/B/R/L) to a color for the given orientation."""
    if top not in _COLOR_VEC or front not in _COLOR_VEC:
        raise ValueError("unknown color")
    if top == front or OPPOSITE[top] == front:
        raise ValueError("invalid orientation: top and front must be adjacent")
    a, b = _COLOR_VEC[top], _COLOR_VEC[front]
    c = _cross(a, b)
    # Rotation M sending (a, b, c) -> (Y, Z, X); M(v) = (v.c, v.a, v.b).
    fcmap: dict[str, str] = {}
    for color, w in _COLOR_VEC.items():
        m = (_dot(w, c), _dot(w, a), _dot(w, b))
        fcmap[S.NORMAL_TO_FACE[m]] = color
    return fcmap


def _build_layout() -> dict[str, list[list[int | None]]]:
    layout: dict[str, list[list[int | None]]] = {
        f: [[None, None, None], [None, None, None], [None, None, None]]
        for f in S.FACE_NORMALS
    }
    for fid, fl in enumerate(S.FACELETS):
        face = S.NORMAL_TO_FACE[fl.normal]
        col = _dot(fl.pos, _RIGHT[face]) + 1
        row = _dot(fl.pos, _DOWN[face]) + 1
        layout[face][row][col] = fid
    return layout


# Per face: 3x3 grid of facelet ids; None marks the (fixed) center.
NET_LAYOUT = _build_layout()


def net_colors(state: tuple[int, ...],
               face_color: dict[str, str] | None = None) -> dict[str, list[str]]:
    """Map each face to its 9 sticker colors (row-major) for an orientation."""
    fc = face_color or face_colors()
    out: dict[str, list[str]] = {}
    for face in FACE_NET_ORDER:
        cells: list[str] = []
        for row in NET_LAYOUT[face]:
            for fid in row:
                if fid is None:
                    cells.append(fc[face])  # center
                else:
                    solved_face = S.NORMAL_TO_FACE[S.FACELETS[state[fid]].normal]
                    cells.append(fc[solved_face])
        out[face] = cells
    return out
