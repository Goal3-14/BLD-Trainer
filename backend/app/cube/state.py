"""N x N x N cube state model (3x3, 4x4, 5x5).

Facelet-permutation model derived from cube geometry. Moves are generated once
from spatial rotations, so the move tables are correct *by construction* rather
than hand-transcribed. Correctness is locked down by the invariant + ground-truth
tests in ``tests/test_cube.py``.

Coordinate system (right-handed):

    +X = R (red)     -X = L (orange)
    +Y = U (white)   -Y = D (yellow)
    +Z = F (green)   -Z = B (blue)

Layers sit at the odd integers ``2i - (n-1)``, so the outer layer is at
``|c| == n-1`` and a middle layer (``c == 0``) exists only for odd ``n``. That
one fact decides which pieces a cube has:

    corner   3 outer coords
    edge     2 outer + a zero        (the 3x3 edge; the 5x5 "midge")
    wing     2 outer + 1 inner       (4x4 and 5x5 only)
    xcenter  1 outer + 2 inner       (4x4 and 5x5; the 4x4 "centre")
    tcenter  1 outer + 1 inner + 1 zero   (5x5 only)
    center   1 outer + 2 zeros       (fixed; never moves, so not tracked)

So 4x4 has no edges, t-centres or fixed centres because an even cube has no
zero coordinate — they are not removed, they cannot exist.

Fixed centres are excluded from the state everywhere: under face and wide moves
they never move, on any size. That keeps the 3x3 state at 48 facelets.

A *facelet* is a single coloured sticker, identified by its cubie position
``pos`` and outward ``normal``. ``state[p]`` is the id of the solved-sticker
currently occupying facelet position ``p``; the solved state is ``(0, 1, ...)``.
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

# Facelet blocks are laid out in this order. Corners then edges first, so the
# 3x3 ids are exactly what they were before the model was generalised.
KIND_ORDER = ("corner", "edge", "wing", "xcenter", "tcenter")


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


def clockwise_quarter(face: str) -> tuple[int, int]:
    """(axis, quarter) for a clockwise turn of ``face`` seen from outside it.

    The single source of this convention: the move tables use it, and so does
    wing lettering, whose chirality is defined as "clockwise about the face".
    """
    normal = FACE_NORMALS[face]
    axis = next(i for i in range(3) if normal[i] != 0)
    return axis, -normal[axis]


def rotate(v: Vec, axis: int, quarter: int) -> Vec:
    return _rotate(v, axis, quarter)


@dataclass(frozen=True)
class Facelet:
    pos: Vec  # cubie position
    normal: Vec  # outward sticker normal
    kind: str  # one of KIND_ORDER
    color: str  # solved color


def _dot3(a: Vec, b: Vec) -> int:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross3(a: Vec, b: Vec) -> Vec:
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


class CubeModel:
    """Geometry, move tables and cubie views for one cube size."""

    def __init__(self, n: int) -> None:
        if n < 3:
            raise ValueError("cube size must be at least 3")
        self.n = n
        self.outer = n - 1
        self.coords: tuple[int, ...] = tuple(2 * i - (n - 1) for i in range(n))
        # Widest turn worth having: 3x3 needs only outer turns, bigger cubes add
        # the two-layer wide turn. A three-layer turn on 5x5 is the same state as
        # a two-layer turn from the far side, so it buys nothing.
        self.max_depth = 1 if n == 3 else 2

        self.facelets: list[Facelet] = self._build_facelets()
        self.N = len(self.facelets)
        self._index: dict[tuple[Vec, Vec], int] = {
            (f.pos, f.normal): i for i, f in enumerate(self.facelets)
        }
        self.SOLVED: tuple[int, ...] = tuple(range(self.N))
        self.ids_by_kind: dict[str, list[int]] = {
            k: [i for i, f in enumerate(self.facelets) if f.kind == k] for k in KIND_ORDER
        }
        self.MOVES: dict[str, list[int]] = self._build_moves()

        self.facelets_at: dict[Vec, list[int]] = {}
        for i, f in enumerate(self.facelets):
            self.facelets_at.setdefault(f.pos, []).append(i)
        self.positions_by_kind: dict[str, list[Vec]] = {}
        for k in KIND_ORDER:
            seen: list[Vec] = []
            for i in self.ids_by_kind[k]:
                if self.facelets[i].pos not in seen:
                    seen.append(self.facelets[i].pos)
            self.positions_by_kind[k] = seen

        self.cubie_of: list[Vec] = [f.pos for f in self.facelets]
        self.cubie_stickers: dict[Vec, tuple[int, ...]] = {
            pos: self._cw_order(pos) for pos in self.facelets_at
        }

        # Colour signatures identify a piece only where its colours are unique:
        # true for corners and edges, false for wings (two wings share a colour
        # pair) and centres (four share a colour).
        self.sig_by_kind: dict[str, dict[frozenset[str], int]] = {}
        for k in ("corner", "edge"):
            positions = self.positions_by_kind[k]
            sig = {
                frozenset(self.facelets[i].color for i in self.facelets_at[pos]): idx
                for idx, pos in enumerate(positions)
            }
            if len(sig) == len(positions):
                self.sig_by_kind[k] = sig

    # --- construction --------------------------------------------------------

    def _classify(self, pos: Vec) -> str | None:
        outer = sum(1 for c in pos if abs(c) == self.outer)
        zeros = sum(1 for c in pos if c == 0)
        if outer == 3:
            return "corner"
        if outer == 2:
            return "edge" if zeros == 1 else "wing"
        if outer == 1:
            if zeros == 2:
                return None  # fixed centre: never moves, not part of the state
            return "tcenter" if zeros == 1 else "xcenter"
        return None  # interior

    def _build_facelets(self) -> list[Facelet]:
        buckets: dict[str, list[Facelet]] = {k: [] for k in KIND_ORDER}
        for x in self.coords:
            for y in self.coords:
                for z in self.coords:
                    pos: Vec = (x, y, z)
                    kind = self._classify(pos)
                    if kind is None:
                        continue
                    for axis in range(3):
                        if abs(pos[axis]) == self.outer:
                            normal: Vec = tuple(  # type: ignore[assignment]
                                (1 if pos[axis] > 0 else -1) if i == axis else 0
                                for i in range(3)
                            )
                            color = FACE_COLORS[NORMAL_TO_FACE[normal]]
                            buckets[kind].append(Facelet(pos, normal, kind, color))
        return [f for k in KIND_ORDER for f in buckets[k]]

    def _move_perm(self, face: str, depth: int) -> list[int]:
        """Destination permutation for a clockwise quarter turn of the outermost
        ``depth`` layers of ``face``. ``dst[i]`` is where the sticker at ``i`` goes."""
        normal = FACE_NORMALS[face]
        axis = next(i for i in range(3) if normal[i] != 0)
        layer_sign = normal[axis]
        quarter = -layer_sign  # clockwise as viewed from outside the face
        cutoff = self.outer - 2 * (depth - 1)
        dst = list(range(self.N))
        for i, f in enumerate(self.facelets):
            if layer_sign * f.pos[axis] >= cutoff:
                new_pos = _rotate(f.pos, axis, quarter)
                new_normal = _rotate(f.normal, axis, quarter)
                dst[i] = self._index[(new_pos, new_normal)]
        return dst

    def _build_moves(self) -> dict[str, list[int]]:
        moves: dict[str, list[int]] = {}
        for face in FACE_ORDER:
            for depth in range(1, self.max_depth + 1):
                name = face if depth == 1 else face + "w"
                base = self._move_perm(face, depth)
                moves[name] = base
                moves[name + "'"] = _invert(base)
                moves[name + "2"] = _square(base)
        return moves

    def _cw_order(self, pos: Vec) -> tuple[int, ...]:
        """A cubie's facelet ids. Corners: clockwise as seen from outside, so a
        swap aligned by this order is a genuine piece rotation. Two-sticker and
        one-sticker pieces: as found (relative order is immaterial)."""
        fids = self.facelets_at[pos]
        if len(fids) < 3:
            return tuple(fids)
        a, b, c = fids
        na, nb = self.facelets[a].normal, self.facelets[b].normal
        # Want a->b clockwise viewed from outside: (na x nb) . pos < 0; else swap.
        if _dot3(_cross3(na, nb), pos) > 0:
            b, c = c, b
        return (a, b, c)

    # --- operations ----------------------------------------------------------

    def facelet_id(self, pos: Vec, normal: Vec) -> int:
        return self._index[(pos, normal)]

    def apply_move(self, state: tuple[int, ...], name: str) -> tuple[int, ...]:
        perm = self.MOVES[name]
        new = [0] * self.N
        for i in range(self.N):
            new[perm[i]] = state[i]
        return tuple(new)

    def apply_sequence(self, state: tuple[int, ...], moves: list[str]) -> tuple[int, ...]:
        for m in moves:
            state = self.apply_move(state, m)
        return state

    def scramble_state(self, moves: list[str]) -> tuple[int, ...]:
        return self.apply_sequence(self.SOLVED, moves)

    def is_solved(self, state: tuple[int, ...]) -> bool:
        """Solved means every sticker shows its home *colour*.

        Not sticker identity: a 4x4's four same-colour centres are
        interchangeable, so demanding each return to its exact slot would reject
        genuinely solved cubes. On 3x3 the two tests agree, since a
        colour-correct 3x3 is solved.
        """
        return all(self.facelets[state[i]].color == self.facelets[i].color
                   for i in range(self.N))

    def cubie_solved(self, w: list[int] | tuple[int, ...], pos: Vec) -> bool:
        """Every sticker of this cubie shows its home colour.

        Per *cubie*, never per sticker: one white sticker sitting in another
        white sticker's slot is not a solved corner. Per cubie it is exactly
        right on every kind — and it is what makes a 4x4's identical wings and
        centres interchangeable, since swapping two of them is invisible.
        """
        return all(self.facelets[w[f]].color == self.facelets[f].color
                   for f in self.facelets_at[pos])

    def orbit_solved(self, w: list[int] | tuple[int, ...], kind: str) -> bool:
        return all(self.cubie_solved(w, pos) for pos in self.positions_by_kind[kind])

    def piece_permutation(self, state: tuple[int, ...], kind: str) -> list[int]:
        """Map each home cubie slot -> index of the piece now occupying it.
        Only defined where colour signatures identify a piece (corners, edges)."""
        sig = self.sig_by_kind[kind]
        perm: list[int] = []
        for pos in self.positions_by_kind[kind]:
            colors = frozenset(self.facelets[state[i]].color for i in self.facelets_at[pos])
            perm.append(sig[colors])
        return perm

    def piece_swap(self, w: list[int], buffer_fid: int, target_fid: int) -> None:
        """The elementary BLD 'shot': swap the whole piece at the buffer with the
        piece at the target sticker, aligning buffer->target and following each
        cubie's sticker order. Moves all of a piece's stickers together with the
        correct orientation, so one shot places a whole piece."""
        b_order = self.cubie_stickers[self.cubie_of[buffer_fid]]
        t_order = self.cubie_stickers[self.cubie_of[target_fid]]
        bi = b_order.index(buffer_fid)
        ti = t_order.index(target_fid)
        k = len(b_order)
        for j in range(k):
            b = b_order[(bi + j) % k]
            t = t_order[(ti + j) % k]
            w[b], w[t] = w[t], w[b]


def _invert(perm: list[int]) -> list[int]:
    inv = [0] * len(perm)
    for i, p in enumerate(perm):
        inv[p] = i
    return inv


def _square(perm: list[int]) -> list[int]:
    return [perm[perm[i]] for i in range(len(perm))]


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


def invert_move(name: str) -> str:
    if name.endswith("2"):
        return name
    if name.endswith("'"):
        return name[:-1]
    return name + "'"


def invert_sequence(moves: list[str]) -> list[str]:
    return [invert_move(m) for m in reversed(moves)]


MODELS: dict[int, CubeModel] = {n: CubeModel(n) for n in (3, 4, 5)}


def model(n: int = 3) -> CubeModel:
    return MODELS[n]


# --- 3x3 surface -------------------------------------------------------------
# The rest of the engine is still 3x3-only, so the original module-level names
# stay bound to the 3x3 model and behave exactly as before.

CUBE3 = MODELS[3]

FACELETS: list[Facelet] = CUBE3.facelets
N: int = CUBE3.N
OUTER: int = CUBE3.outer
SOLVED: tuple[int, ...] = CUBE3.SOLVED
MOVES: dict[str, list[int]] = CUBE3.MOVES
CORNER_IDS: list[int] = CUBE3.ids_by_kind["corner"]
EDGE_IDS: list[int] = CUBE3.ids_by_kind["edge"]
CORNER_POS: list[Vec] = CUBE3.positions_by_kind["corner"]
EDGE_POS: list[Vec] = CUBE3.positions_by_kind["edge"]
CUBIE_OF: list[Vec] = CUBE3.cubie_of
CUBIE_STICKERS: dict[Vec, tuple[int, ...]] = CUBE3.cubie_stickers

facelet_id = CUBE3.facelet_id
apply_move = CUBE3.apply_move
apply_sequence = CUBE3.apply_sequence
scramble_state = CUBE3.scramble_state
is_solved = CUBE3.is_solved
piece_swap = CUBE3.piece_swap


def corner_permutation(state: tuple[int, ...]) -> list[int]:
    return CUBE3.piece_permutation(state, "corner")


def edge_permutation(state: tuple[int, ...]) -> list[int]:
    return CUBE3.piece_permutation(state, "edge")
