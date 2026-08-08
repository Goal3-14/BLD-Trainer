"""4x4 and 5x5 geometry, moves and the colour-based notion of solved.

The 3x3 suite is the regression gate for what already worked; this file locks
down what the generalised model adds. Piece counts are asserted against the
sticker arithmetic (6 * n^2 minus the fixed centres) rather than restated from
the code, so a wrong classification cannot pass.
"""
import random

import pytest

from app.cube import state as S

SIZES = [3, 4, 5]


@pytest.mark.parametrize("n", SIZES)
def test_facelet_count_matches_sticker_arithmetic(n):
    """Every sticker except the fixed centres, which never move."""
    cube = S.model(n)
    fixed_centers = 6 if n % 2 else 0
    assert cube.N == 6 * n * n - fixed_centers


def test_piece_kinds_present_per_size():
    # An even cube has no zero coordinate, so no edges, t-centres or fixed
    # centres can exist. That is the whole difference between 4x4 and 5x5.
    counts = {n: {k: len(S.model(n).ids_by_kind[k]) for k in S.KIND_ORDER} for n in SIZES}
    assert counts[3] == {"corner": 24, "edge": 24, "wing": 0, "xcenter": 0, "tcenter": 0}
    assert counts[4] == {"corner": 24, "edge": 0, "wing": 48, "xcenter": 24, "tcenter": 0}
    assert counts[5] == {"corner": 24, "edge": 24, "wing": 48, "xcenter": 24, "tcenter": 24}


def test_piece_counts_from_stickers_per_piece():
    """24 wings and 24 x-centres as *pieces*, whatever their sticker counts."""
    for n in (4, 5):
        cube = S.model(n)
        assert len(cube.positions_by_kind["wing"]) == 24
        assert len(cube.positions_by_kind["xcenter"]) == 24
        assert len(cube.ids_by_kind["wing"]) == 48  # two stickers each
        assert len(cube.ids_by_kind["xcenter"]) == 24  # one sticker each
    assert len(S.model(5).positions_by_kind["tcenter"]) == 24


def test_move_sets():
    assert len(S.model(3).MOVES) == 18  # 6 faces x {cw, ccw, double}, no wide
    assert "Rw" not in S.model(3).MOVES
    for n in (4, 5):
        assert len(S.model(n).MOVES) == 36  # the same again with wide turns
        assert "Rw" in S.model(n).MOVES and "Rw'" in S.model(n).MOVES


@pytest.mark.parametrize("n", SIZES)
def test_every_move_has_order_four(n):
    cube = S.model(n)
    for name in cube.MOVES:
        reps = 2 if name.endswith("2") else 4
        assert cube.is_solved(cube.scramble_state([name] * reps)), name


@pytest.mark.parametrize("n", SIZES)
def test_random_sequence_then_inverse(n):
    cube = S.model(n)
    names = list(cube.MOVES)
    rng = random.Random(n)
    for _ in range(20):
        seq = [rng.choice(names) for _ in range(25)]
        st = cube.scramble_state(seq)
        st = cube.apply_sequence(st, S.invert_sequence(seq))
        assert cube.is_solved(st)


def _face_row_colors(cube, state, face, depth):
    """Colours on one row of a side face: depth 0 is the row nearest U."""
    normal = S.FACE_NORMALS[face]
    y = cube.outer - 2 * depth
    return {
        cube.facelets[state[i]].color
        for i, f in enumerate(cube.facelets)
        if f.normal == normal and f.pos[1] == y
    }


@pytest.mark.parametrize("n", SIZES)
def test_u_turn_direction_ground_truth(n):
    """U clockwise cycles the side faces F<-R, R<-B, B<-L, L<-F, on every size."""
    cube = S.model(n)
    st = cube.scramble_state(["U"])
    assert _face_row_colors(cube, st, "F", 0) == {"red"}
    assert _face_row_colors(cube, st, "R", 0) == {"blue"}
    assert _face_row_colors(cube, st, "B", 0) == {"orange"}
    assert _face_row_colors(cube, st, "L", 0) == {"green"}


@pytest.mark.parametrize("n", (4, 5))
def test_wide_turn_takes_exactly_two_layers(n):
    cube = S.model(n)
    outer_only = cube.scramble_state(["U"])
    wide = cube.scramble_state(["Uw"])
    # The outer row turns either way; the second row only turns for the wide one.
    assert _face_row_colors(cube, outer_only, "F", 0) == {"red"}
    assert _face_row_colors(cube, outer_only, "F", 1) == {"green"}
    assert _face_row_colors(cube, wide, "F", 0) == {"red"}
    assert _face_row_colors(cube, wide, "F", 1) == {"red"}
    # A third row, where one exists, must be untouched by a two-layer turn.
    if n == 5:
        assert _face_row_colors(cube, wide, "F", 2) == {"green"}


@pytest.mark.parametrize("n", (4, 5))
def test_inner_layer_alone_via_wide_minus_outer(n):
    """Uw then U' leaves the outer layer home and turns only the second layer."""
    cube = S.model(n)
    st = cube.apply_sequence(cube.scramble_state(["Uw"]), ["U'"])
    assert _face_row_colors(cube, st, "F", 0) == {"green"}
    assert _face_row_colors(cube, st, "F", 1) == {"red"}


def test_fixed_centers_are_not_part_of_the_state():
    """5x5 keeps its 6 fixed centres out of the model; they never move."""
    cube = S.model(5)
    assert all(f.kind != "center" for f in cube.facelets)
    # One sticker per face is missing from the state: 150 - 6.
    assert cube.N == 144


def test_same_colour_centres_are_interchangeable_on_4x4():
    """The point of colour-based solving: a 4x4's four same-colour centres are
    identical pieces, so a cube with two of them swapped is genuinely solved."""
    cube = S.model(4)
    white = [i for i in cube.ids_by_kind["xcenter"] if cube.facelets[i].color == "white"]
    assert len(white) == 4
    st = list(cube.SOLVED)
    st[white[0]], st[white[1]] = st[white[1]], st[white[0]]
    assert tuple(st) != cube.SOLVED  # not the identity permutation
    assert cube.is_solved(tuple(st))  # but solved all the same


def test_colour_solved_agrees_with_identity_on_3x3():
    """On 3x3 the two notions coincide, so the new rule changed no behaviour."""
    cube = S.model(3)
    names = list(cube.MOVES)
    rng = random.Random(7)
    assert cube.is_solved(cube.SOLVED)
    for _ in range(300):
        seq = [rng.choice(names) for _ in range(rng.randint(0, 4))]
        st = cube.scramble_state(seq)
        assert cube.is_solved(st) == (st == cube.SOLVED)


@pytest.mark.parametrize("n", (4, 5))
def test_a_scramble_actually_scrambles(n):
    cube = S.model(n)
    rng = random.Random(n * 11)
    names = list(cube.MOVES)
    st = cube.scramble_state([rng.choice(names) for _ in range(30)])
    assert not cube.is_solved(st)


@pytest.mark.parametrize("n", SIZES)
def test_moves_are_permutations(n):
    cube = S.model(n)
    for name, perm in cube.MOVES.items():
        assert sorted(perm) == list(range(cube.N)), name


@pytest.mark.parametrize("n", SIZES)
def test_moves_preserve_piece_kind(n):
    """No move may turn a wing into a centre or a corner into an edge."""
    cube = S.model(n)
    for name in cube.MOVES:
        st = cube.scramble_state([name])
        for i, fid in enumerate(st):
            assert cube.facelets[fid].kind == cube.facelets[i].kind, name
