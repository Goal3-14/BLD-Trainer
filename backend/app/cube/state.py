"""3x3 cube state model.

Facelet-permutation model derived from cube geometry. The 18 face moves are
generated once from spatial rotations, so the move tables are correct *by
construction* rather than hand-transcribed. Correctness is locked down by the
invariant + ground-truth tests in ``tests/test_cube.py``.

Coordinate system (right-handed):

    +X = R (red)     -X = L (orange)
    +Y = U (white)   -Y = D (yellow)
    +Z = F (green)   -Z = B (blue)

A *facelet* is a single colored sticker on a corner or edge cubie, identified
by its cubie position ``pos`` and outward ``normal`` (both in {-1,0,1}^3).
Centers are fixed under face moves and are not part of the movable state.

State representation: a tuple of length 48. ``state[p]`` is the id of the
solved-sticker currently occupying facelet position ``p``. The solved state is
``(0, 1, ..., 47)``.
"""
from __future__ import annotations

from dataclasses import dataclass

Vec = tuple[int, int, int]

FACE_NORMALS: dict[str, Vec] = {
    "U": (0, 1, 0),
    "D": (0, -1, 0),
    "F": (0, 0, 1),
    "B": (0, 0, -1),
    "R": (1, 0, 0),
    "L": (-1, 0, 0),
}
FACE_COLORS: dict[str, str] = {
    "U": "white",
    "D": "yellow",
    "F": "green",
    "B": "blue",
    "R": "red",
    "L": "orange",
}
NORMAL_TO_FACE: dict[Vec, str] = {v: k for k, v in FACE_NORMALS.items()}

FACE_ORDER = "UDFBRL"


def _rotate(v: Vec, axis: int, quarter: int) -> Vec:
    """Rotate ``v`` by ``quarter`` * 90 degrees (right-hand rule) about a coordinate axis."""
    x, y, z = v
    for _ in range(quarter % 4):
        if axis == 0:  # +90 about X: (x, -z, y)
            x, y, z = x, -z, y
        elif axis == 1:  # +90 about Y: (z, y, -x)
            x, y, z = z, y, -x
        else:  # +90 about Z: (-y, x, z)
            x, y, z = -y, x, z
    return (x, y, z)


@dataclass(frozen=True)
class Facelet:
    pos: Vec  # cubie position
    normal: Vec  # outward sticker normal
    kind: str  # "corner" | "edge"
    color: str  # solved color


def _build_facelets() -> list[Facelet]:
    """All 48 movable facelets: 24 corner-stickers, then 24 edge-stickers."""
    corners: list[Facelet] = []
    edges: list[Facelet] = []
    for x in (-1, 0, 1):
        for y in (-1, 0, 1):
            for z in (-1, 0, 1):
                pos = (x, y, z)
                nonzero = [c for c in pos if c != 0]
                if len(nonzero) < 2:
                    continue  # core or center -> not movable
                kind = "corner" if len(nonzero) == 3 else "edge"
                bucket = corners if kind == "corner" else edges
                for axis in range(3):
                    if pos[axis] != 0:
                        normal: Vec = tuple(pos[axis] if i == axis else 0 for i in range(3))  # type: ignore[assignment]
                        color = FACE_COLORS[NORMAL_TO_FACE[normal]]
                        bucket.append(Facelet(pos, normal, kind, color))
    return corners + edges


FACELETS: list[Facelet] = _build_facelets()
N: int = len(FACELETS)
_INDEX: dict[tuple[Vec, Vec], int] = {(f.pos, f.normal): i for i, f in enumerate(FACELETS)}

CORNER_IDS: list[int] = [i for i, f in enumerate(FACELETS) if f.kind == "corner"]
EDGE_IDS: list[int] = [i for i, f in enumerate(FACELETS) if f.kind == "edge"]

SOLVED: tuple[int, ...] = tuple(range(N))


def facelet_id(pos: Vec, normal: Vec) -> int:
    """Engine facelet id for the sticker at cubie position ``pos`` with outward ``normal``."""
    return _INDEX[(pos, normal)]


def _base_move_perm(face: str) -> list[int]:
    """Destination permutation for a clockwise quarter turn of ``face``.

    ``dst[i]`` = the facelet position that the sticker currently at ``i`` moves to.
    """
    normal = FACE_NORMALS[face]
    axis = next(i for i in range(3) if normal[i] != 0)
    layer_sign = normal[axis]
    quarter = -layer_sign  # clockwise as viewed from outside the face
    dst = list(range(N))
    for i, f in enumerate(FACELETS):
        if f.pos[axis] == layer_sign:
            new_pos = _rotate(f.pos, axis, quarter)
            new_normal = _rotate(f.normal, axis, quarter)
            dst[i] = _INDEX[(new_pos, new_normal)]
    return dst


def _invert(perm: list[int]) -> list[int]:
    inv = [0] * len(perm)
    for i, p in enumerate(perm):
        inv[p] = i
    return inv


def _square(perm: list[int]) -> list[int]:
    return [perm[perm[i]] for i in range(len(perm))]


MOVES: dict[str, list[int]] = {}
for _face in FACE_ORDER:
    _base = _base_move_perm(_face)
    MOVES[_face] = _base
    MOVES[_face + "'"] = _invert(_base)
    MOVES[_face + "2"] = _square(_base)


def apply_move(state: tuple[int, ...], name: str) -> tuple[int, ...]:
    perm = MOVES[name]
    new = [0] * N
    for i in range(N):
        new[perm[i]] = state[i]
    return tuple(new)


def apply_sequence(state: tuple[int, ...], moves: list[str]) -> tuple[int, ...]:
    for m in moves:
        state = apply_move(state, m)
    return state


def scramble_state(moves: list[str]) -> tuple[int, ...]:
    """Apply a move sequence to the solved cube."""
    return apply_sequence(SOLVED, moves)


def is_solved(state: tuple[int, ...]) -> bool:
    return tuple(state) == SOLVED


def invert_move(name: str) -> str:
    if name.endswith("2"):
        return name
    if name.endswith("'"):
        return name[:-1]
    return name + "'"


def invert_sequence(moves: list[str]) -> list[str]:
    return [invert_move(m) for m in reversed(moves)]


# --- Cubie-level views (for invariants and, later, tracing) -------------------

def _cubie_positions(kind: str) -> list[Vec]:
    seen: list[Vec] = []
    for f in FACELETS:
        if f.kind == kind and f.pos not in seen:
            seen.append(f.pos)
    return seen


CORNER_POS: list[Vec] = _cubie_positions("corner")
EDGE_POS: list[Vec] = _cubie_positions("edge")

# Each cubie is uniquely identified by the frozenset of its solved sticker colors.
_FACELETS_AT: dict[Vec, list[int]] = {}
for _i, _f in enumerate(FACELETS):
    _FACELETS_AT.setdefault(_f.pos, []).append(_i)

_CORNER_SIG: dict[frozenset[str], int] = {
    frozenset(FACELETS[i].color for i in _FACELETS_AT[pos]): k
    for k, pos in enumerate(CORNER_POS)
}
_EDGE_SIG: dict[frozenset[str], int] = {
    frozenset(FACELETS[i].color for i in _FACELETS_AT[pos]): k
    for k, pos in enumerate(EDGE_POS)
}


def _piece_permutation(state: tuple[int, ...], positions: list[Vec],
                       sig: dict[frozenset[str], int]) -> list[int]:
    """Map each home cubie slot -> index of the piece currently occupying it."""
    perm: list[int] = []
    for pos in positions:
        colors = frozenset(FACELETS[state[i]].color for i in _FACELETS_AT[pos])
        perm.append(sig[colors])
    return perm


def corner_permutation(state: tuple[int, ...]) -> list[int]:
    return _piece_permutation(state, CORNER_POS, _CORNER_SIG)


def edge_permutation(state: tuple[int, ...]) -> list[int]:
    return _piece_permutation(state, EDGE_POS, _EDGE_SIG)


def permutation_parity(perm: list[int]) -> int:
    """0 if even, 1 if odd."""
    seen = [False] * len(perm)
    parity = 0
    for i in range(len(perm)):
        if seen[i]:
            continue
        length = 0
        j = i
        while not seen[j]:
            seen[j] = True
            j = perm[j]
            length += 1
        parity ^= (length - 1) & 1
    return parity


# --- Cubie sticker ordering + piece swap (for piece-level BLD operations) -----

def _dot3(a: Vec, b: Vec) -> int:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross3(a: Vec, b: Vec) -> Vec:
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _cw_order(pos: Vec) -> tuple[int, ...]:
    """A cubie's facelet ids. Corners: clockwise as seen from outside, so a
    swap aligned by this order is a genuine piece rotation. Edges: the two
    stickers (relative order is immaterial)."""
    fids = _FACELETS_AT[pos]
    if len(fids) == 2:
        return tuple(fids)
    a, b, c = fids
    na, nb = FACELETS[a].normal, FACELETS[b].normal
    # Want a->b clockwise viewed from outside: (na x nb) . pos < 0; else swap.
    if _dot3(_cross3(na, nb), pos) > 0:
        b, c = c, b
    return (a, b, c)


CUBIE_OF: list[Vec] = [f.pos for f in FACELETS]
CUBIE_STICKERS: dict[Vec, tuple[int, ...]] = {
    pos: _cw_order(pos) for pos in (CORNER_POS + EDGE_POS)
}


def piece_swap(w: list[int], buffer_fid: int, target_fid: int) -> None:
    """The elementary BLD 'shot': swap the whole piece at the buffer with the
    piece at the target sticker, aligning buffer->target and following each
    cubie's sticker order. Moves all of a piece's stickers together with the
    correct orientation, so one shot places a whole piece."""
    b_order = CUBIE_STICKERS[CUBIE_OF[buffer_fid]]
    t_order = CUBIE_STICKERS[CUBIE_OF[target_fid]]
    bi = b_order.index(buffer_fid)
    ti = t_order.index(target_fid)
    n = len(b_order)
    for k in range(n):
        p = b_order[(bi + k) % n]
        q = t_order[(ti + k) % n]
        w[p], w[q] = w[q], w[p]
