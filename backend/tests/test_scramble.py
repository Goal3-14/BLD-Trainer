import random

from app.cube import state as S
from app.cube.scramble import _AXIS, generate_scramble


def test_length_and_valid_tokens():
    scr = generate_scramble(length=20, seed=1)
    assert len(scr) == 20
    assert all(tok in S.MOVES for tok in scr)


def test_deterministic_with_seed():
    assert generate_scramble(20, seed=42) == generate_scramble(20, seed=42)


def test_no_redundant_moves():
    for seed in range(50):
        scr = generate_scramble(25, seed=seed)
        faces = [tok[0] for tok in scr]
        for i in range(1, len(faces)):
            assert faces[i] != faces[i - 1]  # no immediate face repeat
        for i in range(2, len(faces)):
            same_axis = _AXIS[faces[i]] == _AXIS[faces[i - 1]] == _AXIS[faces[i - 2]]
            assert not same_axis  # no three-on-an-axis


def test_scramble_actually_scrambles():
    st = S.scramble_state(generate_scramble(20, seed=7))
    assert not S.is_solved(st)


def test_prefix_is_not_included_in_result():
    prefix = generate_scramble(20, seed=11)
    scr = generate_scramble(10, seed=12, prefix=prefix)
    assert len(scr) == 10
    assert all(tok in S.MOVES for tok in scr)


def test_prefix_filters_redundancy_across_the_seam():
    for seed in range(50):
        prefix = generate_scramble(20, seed=seed)
        scr = generate_scramble(20, seed=seed + 1000, prefix=prefix)
        faces = [tok[0] for tok in prefix + scr]
        for i in range(1, len(faces)):
            assert faces[i] != faces[i - 1]
        for i in range(2, len(faces)):
            same_axis = _AXIS[faces[i]] == _AXIS[faces[i - 1]] == _AXIS[faces[i - 2]]
            assert not same_axis


def test_continuing_from_a_scramble_matches_applying_moves_to_that_state():
    """prefix + new applied to solved == new applied to the prefix's state."""
    prefix = generate_scramble(20, seed=3)
    scr = generate_scramble(20, seed=4, prefix=prefix)
    assert S.scramble_state(prefix + scr) == S.apply_sequence(S.scramble_state(prefix), scr)
