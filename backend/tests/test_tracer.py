"""Tracer + validator correctness.

The headline test is the round-trip: trace any scramble, then the memo must
validate as solved. Run over hundreds of random states it exercises cycle
breaks, solved buffers, in-place flips/twists, and parity.
"""
import random

import pytest

from app.cube import state as S
from app.cube.scramble import generate_scramble
from app.cube.tracer import trace
from app.cube.validator import solves, validate


def _random_states(n, seed, max_len=30):
    moves = list(S.MOVES)
    rng = random.Random(seed)
    for _ in range(n):
        scr = [rng.choice(moves) for _ in range(rng.randint(0, max_len))]
        yield S.scramble_state(scr)


def test_trace_validate_roundtrip_random():
    for st in _random_states(500, seed=0):
        memo = trace(st)
        assert solves(st, memo.corners, memo.edges)


def test_trace_validate_roundtrip_real_scrambles():
    for seed in range(100):
        st = S.scramble_state(generate_scramble(20, seed=seed))
        memo = trace(st)
        assert solves(st, memo.corners, memo.edges)


def test_solved_scramble_has_empty_memo():
    memo = trace(S.SOLVED)
    assert memo.corners == [] and memo.edges == []
    assert solves(S.SOLVED, [], [])


def test_parity_flag_matches_piece_permutation():
    # True BLD parity is the odd *piece* permutation (corners and edges always
    # agree). It is NOT the same as memo-length parity, which also counts the
    # sticker cycles created by in-place twists/flips.
    for st in _random_states(300, seed=11):
        memo = trace(st)
        corner_odd = S.permutation_parity(S.corner_permutation(st)) == 1
        edge_odd = S.permutation_parity(S.edge_permutation(st)) == 1
        assert corner_odd == edge_odd  # the invariant the engine guarantees
        assert memo.has_parity == corner_odd


@pytest.mark.parametrize("cb,eb", [("A", "A"), ("C", "C"), ("U", "U"), ("M", "P"), ("X", "G")])
def test_roundtrip_various_buffers(cb, eb):
    for st in _random_states(80, seed=hash((cb, eb)) & 0xFFFF):
        memo = trace(st, corner_buffer=cb, edge_buffer=eb)
        assert solves(st, memo.corners, memo.edges, corner_buffer=cb, edge_buffer=eb)


def test_wrong_memo_fails():
    st = S.scramble_state(generate_scramble(20, seed=3))
    memo = trace(st)
    assert memo.corners and memo.edges  # length-20 scramble leaves work in both orbits
    # Drop a target -> should no longer solve.
    assert not solves(st, memo.corners[:-1], memo.edges)
    assert not solves(st, memo.corners, memo.edges[:-1])


def test_validate_reports_per_orbit():
    st = S.scramble_state(generate_scramble(20, seed=5))
    memo = trace(st)
    v = validate(st, memo.corners, [])  # solve corners only
    assert v.corners_solved and not v.edges_solved and not v.solved
