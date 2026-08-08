"""Tracing and validating 4x4 and 5x5.

The round-trip property is the one that matters: whatever the tracer produces
must validate as solved, on every orbit, for arbitrary scrambles. On the big
cubes it carries more weight than on 3x3, because a centre shot has four
equally valid destinations — there is no canonical memo to compare against, so
simulation is the only thing that could answer the question at all.
"""
import random

import pytest

from app.cube import scheme as SC
from app.cube import state as S
from app.cube.tracer import trace_cube
from app.cube.validator import validate_cube

SIZES = [3, 4, 5]


def _scramble(n, seed, length=30):
    cube = S.model(n)
    rng = random.Random(seed)
    names = list(cube.MOVES)
    return cube.scramble_state([rng.choice(names) for _ in range(length)])


@pytest.mark.parametrize("n", SIZES)
def test_trace_then_validate_solves(n):
    for seed in range(25):
        st = _scramble(n, seed)
        memo = trace_cube(st, n)
        verdict = validate_cube(st, memo.targets, n, memo.buffers)
        assert verdict.solved, (n, seed, verdict.by_orbit)


@pytest.mark.parametrize("n", SIZES)
def test_every_buffer_letter_traces_and_validates(n):
    """Any sticker is a legal buffer, so all 24 must work on every orbit — not
    just the default. Interchangeable pieces made this fail: a cycle break onto
    a slot holding the buffer's own colour swapped two identical stickers and
    never terminated."""
    for seed in range(3):
        st = _scramble(n, 800 + seed)
        for kind in SC.ORBITS[n]:
            for letter in SC.LETTERS:
                memo = trace_cube(st, n, {kind: letter})
                assert validate_cube(st, memo.targets, n, memo.buffers).solved, (
                    n, seed, kind, letter,
                )


@pytest.mark.parametrize("n", SIZES)
def test_memo_covers_exactly_the_orbits_that_exist(n):
    memo = trace_cube(_scramble(n, 1), n)
    assert set(memo.targets) == set(SC.ORBITS[n])
    assert set(memo.buffers) == set(SC.ORBITS[n])


def test_4x4_memo_has_centres_and_wings_but_no_midges():
    memo = trace_cube(_scramble(4, 3), 4)
    assert set(memo.targets) == {"corner", "wing", "xcenter"}
    assert memo.targets["xcenter"] and memo.targets["wing"]


def test_5x5_memo_has_all_five_orbits():
    memo = trace_cube(_scramble(5, 3), 5)
    assert set(memo.targets) == {"corner", "edge", "wing", "xcenter", "tcenter"}
    assert all(memo.targets[k] for k in memo.targets)


@pytest.mark.parametrize("n", SIZES)
def test_solved_cube_needs_no_targets(n):
    memo = trace_cube(S.model(n).SOLVED, n)
    assert all(t == [] for t in memo.targets.values())
    assert validate_cube(S.model(n).SOLVED, memo.targets, n).solved


@pytest.mark.parametrize("n", SIZES)
def test_a_truncated_memo_does_not_validate(n):
    """Guards the round-trip test from passing because validate always says yes."""
    for seed in range(5):
        st = _scramble(n, 100 + seed)
        memo = trace_cube(st, n)
        for kind, targets in memo.targets.items():
            if not targets:
                continue
            short = dict(memo.targets)
            short[kind] = targets[:-1]
            v = validate_cube(st, short, n, memo.buffers)
            assert not v.solved, (n, seed, kind)
            assert not v.by_orbit[kind]


@pytest.mark.parametrize("n", (4, 5))
def test_memo_lengths_are_realistic(n):
    """A shot per piece: 24-piece orbits should not run far past 24 targets."""
    for seed in range(10):
        memo = trace_cube(_scramble(n, 200 + seed), n)
        for kind, targets in memo.targets.items():
            assert len(targets) <= 26, (n, kind, len(targets))


# --- centres really are interchangeable --------------------------------------


def _trace_centres_naively(state, n, kind):
    """Shoot to the home of the sticker held, ignoring that three other slots of
    that colour would do just as well. A different memo, equally valid."""
    cube = S.model(n)
    orbit = SC.ORBITS[n][kind]
    w = list(state)
    ordered = orbit.facelets_in_letter_order
    buffer_fid = orbit.facelet_by_letter[orbit.default_buffer]
    buffer_cubie = cube.cubie_of[buffer_fid]
    targets = []

    for _ in range(len(ordered) * 3 + 20):
        if cube.cubie_solved(w, buffer_cubie):
            target = next(
                (p for p in ordered
                 if cube.cubie_of[p] != buffer_cubie and not cube.cubie_solved(w, cube.cubie_of[p])),
                None,
            )
            if target is None:
                return targets
        else:
            target = w[buffer_fid]
            if cube.cubie_of[target] == buffer_cubie:
                return targets
        targets.append(orbit.letter_by_facelet[target])
        cube.piece_swap(w, buffer_fid, target)
    raise AssertionError("naive centre tracer did not converge")


@pytest.mark.parametrize("n", (4, 5))
def test_a_different_centre_memo_also_validates(n):
    """Two tracers, two different centre memos, both solve the same cube. This
    is what validation-by-simulation buys: no canonical answer is needed."""
    differing = 0
    for seed in range(15):
        st = _scramble(n, 300 + seed)
        memo = trace_cube(st, n)
        naive = dict(memo.targets)
        naive["xcenter"] = _trace_centres_naively(st, n, "xcenter")
        assert validate_cube(st, naive, n, memo.buffers).solved, (n, seed)
        if naive["xcenter"] != memo.targets["xcenter"]:
            differing += 1
    assert differing >= 10, f"only {differing}/15 differed — the test is vacuous"


@pytest.mark.parametrize("n", (4, 5))
def test_choosing_the_target_beats_taking_the_sticker(n):
    """The centre rule exists to shorten memos, so it should actually do that."""
    chosen = naive = 0
    for seed in range(15):
        st = _scramble(n, 400 + seed)
        chosen += len(trace_cube(st, n).targets["xcenter"])
        naive += len(_trace_centres_naively(st, n, "xcenter"))
    assert chosen <= naive, (chosen, naive)


# --- parity ------------------------------------------------------------------


def test_orbit_parity_is_the_target_count():
    """Every shot is a transposition, so an odd target count is an odd
    permutation. Cross-checked against the independent 3x3 computation."""
    for seed in range(30):
        st = _scramble(3, 500 + seed)
        memo = trace_cube(st, 3)
        by_perm = S.permutation_parity(S.corner_permutation(st)) == 1
        assert memo.orbit_parity("corner") == by_perm, seed
        assert memo.parity == by_perm, seed


def test_3x3_corner_and_edge_parity_agree():
    for seed in range(30):
        memo = trace_cube(_scramble(3, 600 + seed), 3)
        assert memo.orbit_parity("corner") == memo.orbit_parity("edge"), seed


@pytest.mark.parametrize("n", (4, 5))
def test_parity_is_reported_per_orbit_on_big_cubes(n):
    """4BLD parity lives between orbits, so each one reports its own."""
    seen = set()
    for seed in range(20):
        memo = trace_cube(_scramble(n, 700 + seed), n)
        for kind in memo.targets:
            seen.add((kind, memo.orbit_parity(kind)))
    # Both parities should show up across enough scrambles, or the notion is
    # not measuring anything.
    for kind in SC.ORBITS[n]:
        assert (kind, True) in seen and (kind, False) in seen, kind
