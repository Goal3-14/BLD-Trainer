"""Cube engine correctness.

Two kinds of checks:
  * Invariants — sensitive to any indexing/composition bug (orders, inverses,
    permutation parity equality unique to face-turn states).
  * Ground truth — pin the move *labels/directions* to a real cube (e.g. what a
    U turn physically does to the side faces), so "R" really means R.
"""
import random

import pytest

from app.cube import state as S


def test_facelet_counts():
    assert S.N == 48
    assert len(S.CORNER_IDS) == 24
    assert len(S.EDGE_IDS) == 24
    assert len(S.MOVES) == 18  # 6 faces x {cw, ccw, double}


def test_solved_roundtrip():
    assert S.is_solved(S.SOLVED)
    assert S.scramble_state([]) == S.SOLVED


@pytest.mark.parametrize("face", list("UDFBRL"))
def test_quarter_turn_order_four(face):
    st = S.scramble_state([face, face, face, face])
    assert S.is_solved(st)


@pytest.mark.parametrize("face", list("UDFBRL"))
def test_double_and_prime(face):
    # F2 == F F
    assert S.scramble_state([face + "2"]) == S.scramble_state([face, face])
    # F F' == solved
    assert S.is_solved(S.scramble_state([face, face + "'"]))
    # F2 F2 == solved
    assert S.is_solved(S.scramble_state([face + "2", face + "2"]))


def test_sexy_move_order_six():
    seq = ["R", "U", "R'", "U'"] * 6
    assert S.is_solved(S.scramble_state(seq))


def test_tperm_is_involution():
    # T-perm swaps two corners and two edges -> applying it twice is identity.
    tperm = ["R", "U", "R'", "U'", "R'", "F", "R2", "U'", "R'", "U'", "R", "U", "R'", "F'"]
    assert S.is_solved(S.scramble_state(tperm * 2))


def test_random_sequence_then_inverse():
    moves = list(S.MOVES.keys())
    rng = random.Random(1234)
    for _ in range(200):
        seq = [rng.choice(moves) for _ in range(25)]
        st = S.scramble_state(seq)
        st = S.apply_sequence(st, S.invert_sequence(seq))
        assert S.is_solved(st)


def test_corner_edge_parity_equal():
    # For any face-turn-only state, corner-permutation parity == edge-permutation
    # parity (each quarter turn is a 4-cycle on both).
    moves = list(S.MOVES.keys())
    rng = random.Random(99)
    for _ in range(300):
        seq = [rng.choice(moves) for _ in range(rng.randint(0, 30))]
        st = S.scramble_state(seq)
        cp = S.permutation_parity(S.corner_permutation(st))
        ep = S.permutation_parity(S.edge_permutation(st))
        assert cp == ep


def _top_row_color(st, face_normal):
    """Color now showing on the top (y==1) stickers of the given side face."""
    colors = {
        S.FACELETS[st[i]].color
        for i, f in enumerate(S.FACELETS)
        if f.normal == face_normal and f.pos[1] == 1
    }
    assert len(colors) == 1, colors
    return colors.pop()


def test_u_turn_direction_ground_truth():
    # U clockwise cycles the side faces F<-R, R<-B, B<-L, L<-F.
    st = S.scramble_state(["U"])
    assert _top_row_color(st, S.FACE_NORMALS["F"]) == "red"  # R -> F
    assert _top_row_color(st, S.FACE_NORMALS["R"]) == "blue"  # B -> R
    assert _top_row_color(st, S.FACE_NORMALS["B"]) == "orange"  # L -> B
    assert _top_row_color(st, S.FACE_NORMALS["L"]) == "green"  # F -> L


def test_centers_color_scheme():
    # Sanity: opposite faces and the white-top/green-front scheme.
    assert S.FACE_COLORS["U"] == "white" and S.FACE_COLORS["D"] == "yellow"
    assert S.FACE_COLORS["F"] == "green" and S.FACE_COLORS["B"] == "blue"
    assert S.FACE_COLORS["R"] == "red" and S.FACE_COLORS["L"] == "orange"
