"""Render a cube state as colors on the standard unfolded net.

The backend owns this (cube logic stays server-side): each face becomes a
row-major list of 9 color names that the frontend draws directly. Centers are
fixed per face; the 8 movable stickers come from the state.

Net orientation (white top / green front), per face right/down world axes:

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


def _dot(a: S.Vec, b: S.Vec) -> int:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


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


def net_colors(state: tuple[int, ...]) -> dict[str, list[str]]:
    """Map each face to its 9 sticker colors (row-major)."""
    out: dict[str, list[str]] = {}
    for face in FACE_NET_ORDER:
        cells: list[str] = []
        for row in NET_LAYOUT[face]:
            for fid in row:
                if fid is None:
                    cells.append(S.FACE_COLORS[face])  # center
                else:
                    cells.append(S.FACELETS[state[fid]].color)
        out[face] = cells
    return out
