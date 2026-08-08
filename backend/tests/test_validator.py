"""Validation must be free of the tracer's choices.

The tracer breaks into the *lowest-letter* unsolved piece, but that is only one
of many valid memos. A solver who breaks into a different piece is not wrong, so
the validator — which replays the given targets as swaps and asks whether the
cube ends solved — must accept those memos too.
"""
from __future__ import annotations

from collections.abc import Callable

from app.cube import scheme as SC
from app.cube import state as S
from app.cube.scramble import generate_scramble
from app.cube.tracer import trace
from app.cube.validator import solves

Choose = Callable[[list[int]], int]


def _trace_choosing_break(state: tuple[int, ...], ordered_facelets: list[int],
                          buffer_fid: int, letter_by_facelet: dict[int, str],
                          choose: Choose) -> list[str]:
    """The tracer's shot rule, but `choose` picks the cycle-break target from
    every unsolved piece rather than always taking the lowest letter."""
    w = list(state)
    targets: list[str] = []
    buffer_cubie = S.CUBIE_OF[buffer_fid]
    buffer_stickers = S.CUBIE_STICKERS[buffer_cubie]

    for _ in range(len(ordered_facelets) * 3 + 20):
        shown = w[buffer_fid]
        buffer_solved = all(w[f] == f for f in buffer_stickers)
        if buffer_solved or S.CUBIE_OF[shown] == buffer_cubie:
            # Buffer piece is done (or home but twisted) -> break into a new cycle.
            options = [p for p in ordered_facelets
                       if S.CUBIE_OF[p] != buffer_cubie and w[p] != p]
            if not options:
                return targets
            target = choose(options)
        else:
            target = shown
        targets.append(letter_by_facelet[target])
        S.piece_swap(w, buffer_fid, target)

    raise AssertionError("alternative tracer did not converge")


def _memo(state: tuple[int, ...], choose: Choose) -> tuple[list[str], list[str]]:
    corners = _trace_choosing_break(
        state, SC.CORNER_FACELETS_IN_LETTER_ORDER,
        SC.CORNER_FACELET_BY_LETTER["C"], SC.CORNER_LETTER_BY_FACELET, choose,
    )
    edges = _trace_choosing_break(
        state, SC.EDGE_FACELETS_IN_LETTER_ORDER,
        SC.EDGE_FACELET_BY_LETTER["C"], SC.EDGE_LETTER_BY_FACELET, choose,
    )
    return corners, edges


_STRATEGIES: dict[str, Choose] = {
    "lowest": lambda opts: opts[0],  # what the tracer does
    "highest": lambda opts: opts[-1],
    "middle": lambda opts: opts[len(opts) // 2],
}


def test_any_cycle_break_choice_validates():
    for seed in range(30):
        st = S.scramble_state(generate_scramble(20, seed=seed))
        for name, choose in _STRATEGIES.items():
            corners, edges = _memo(st, choose)
            assert solves(st, corners, edges), f"seed {seed}, break strategy {name}"


def test_those_choices_really_produce_different_memos():
    """Guards the test above from passing vacuously."""
    differing = 0
    for seed in range(30):
        st = S.scramble_state(generate_scramble(20, seed=seed))
        mine = _memo(st, _STRATEGIES["highest"])
        theirs = trace(st)
        if mine != (theirs.corners, theirs.edges):
            differing += 1
    assert differing > 20, f"only {differing}/30 memos differed from the tracer"


def test_the_lowest_strategy_reproduces_the_tracer():
    """Anchors the alternative tracer to the real one: same rule, same result."""
    for seed in range(30):
        st = S.scramble_state(generate_scramble(20, seed=seed))
        m = trace(st)
        assert _memo(st, _STRATEGIES["lowest"]) == (m.corners, m.edges)
