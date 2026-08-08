"""Big-cube scrambles: wide moves only, never a bare inner-slice turn."""
import re

import pytest

from app.cube import state as S
from app.cube.scramble import _AXIS, generate_scramble
from app.cube.tracer import trace_cube
from app.cube.validator import validate_cube

SIZES = [3, 4, 5]


@pytest.mark.parametrize("n", SIZES)
def test_tokens_are_legal_moves_for_that_size(n):
    scr = generate_scramble(seed=1, n=n)
    assert all(tok in S.model(n).MOVES for tok in scr)


def test_only_3x3_lacks_wide_moves():
    assert not any("w" in t for t in generate_scramble(200, seed=2, n=3))
    for n in (4, 5):
        assert any("w" in t for t in generate_scramble(200, seed=2, n=n))


@pytest.mark.parametrize("n", SIZES)
def test_no_slice_only_notation(n):
    """Only U/R/F/D/L/B, optionally wide — never r, u, l, M, E or S."""
    token = re.compile(r"^[URFDLB]w?(?:'|2)?$")
    for tok in generate_scramble(200, seed=3, n=n):
        assert token.match(tok), tok


@pytest.mark.parametrize("n", SIZES)
def test_no_disguised_inner_slice_turn(n):
    """`R Rw'` would net to a bare inner-slice turn, so consecutive turns of the
    same face are rejected at any width."""
    for seed in range(30):
        faces = [t[0] for t in generate_scramble(60, seed=seed, n=n)]
        for i in range(1, len(faces)):
            assert faces[i] != faces[i - 1]
        for i in range(2, len(faces)):
            assert not (_AXIS[faces[i]] == _AXIS[faces[i - 1]] == _AXIS[faces[i - 2]])


def _no_opposite_wide_pair(moves):
    """`Uw Dw'` means regripping the whole cube twice over — never emit it."""
    for a, b in zip(moves, moves[1:]):
        if "w" in a and "w" in b:
            assert _AXIS[a[0]] != _AXIS[b[0]], f"{a} {b}"


@pytest.mark.parametrize("n", (4, 5))
def test_no_wide_move_follows_a_wide_move_on_the_opposite_face(n):
    for seed in range(40):
        _no_opposite_wide_pair(generate_scramble(120, seed=seed, n=n))


@pytest.mark.parametrize("n", (4, 5))
def test_wide_moves_are_still_common(n):
    """The rule must not quietly starve the scramble of wide moves."""
    scr = generate_scramble(400, seed=11, n=n)
    wide = sum(1 for t in scr if "w" in t)
    assert 0.35 < wide / len(scr) < 0.65, wide / len(scr)


@pytest.mark.parametrize("n", SIZES)
def test_prefix_filters_redundancy_across_the_seam(n):
    for seed in range(20):
        prefix = generate_scramble(30, seed=seed, n=n)
        scr = generate_scramble(30, seed=seed + 900, prefix=prefix, n=n)
        faces = [t[0] for t in prefix + scr]
        for i in range(1, len(faces)):
            assert faces[i] != faces[i - 1]
        _no_opposite_wide_pair(prefix + scr)  # including across the seam


@pytest.mark.parametrize("n", SIZES)
def test_continuing_matches_applying_moves_to_that_state(n):
    cube = S.model(n)
    prefix = generate_scramble(30, seed=4, n=n)
    scr = generate_scramble(30, seed=5, prefix=prefix, n=n)
    assert cube.scramble_state(prefix + scr) == cube.apply_sequence(
        cube.scramble_state(prefix), scr
    )


@pytest.mark.parametrize("n", SIZES)
def test_scramble_actually_scrambles_every_orbit(n):
    """A scramble that left an orbit solved would silently skip that memo."""
    cube = S.model(n)
    for seed in range(10):
        st = cube.scramble_state(generate_scramble(seed=seed, n=n))
        assert not cube.is_solved(st)
        for kind in cube.positions_by_kind:
            if cube.positions_by_kind[kind]:
                assert not cube.orbit_solved(st, kind), (n, seed, kind)


@pytest.mark.parametrize("n", SIZES)
def test_generated_scrambles_trace_and_validate(n):
    for seed in range(10):
        st = S.model(n).scramble_state(generate_scramble(seed=seed, n=n))
        memo = trace_cube(st, n)
        assert validate_cube(st, memo.targets, n, memo.buffers).solved


def test_default_lengths_scale_with_size():
    assert len(generate_scramble(seed=1, n=3)) == 20
    assert len(generate_scramble(seed=1, n=4)) == 40
    assert len(generate_scramble(seed=1, n=5)) == 60


def test_deterministic_with_seed():
    for n in SIZES:
        assert generate_scramble(seed=42, n=n) == generate_scramble(seed=42, n=n)
