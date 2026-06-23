import pytest

from app.cube import state as S
from app.cube.net import COLORS, OPPOSITE, face_colors, net_colors


def test_default_matches_standard_scheme():
    assert face_colors() == {f: S.FACE_COLORS[f] for f in S.FACE_NORMALS}


def test_all_valid_orientations_are_bijective():
    valid = 0
    for top in COLORS:
        for front in COLORS:
            if top == front or OPPOSITE[top] == front:
                with pytest.raises(ValueError):
                    face_colors(top, front)
                continue
            fc = face_colors(top, front)
            assert set(fc.values()) == set(COLORS)  # all six colors, no repeats
            assert fc["U"] == top
            assert fc["F"] == front
            assert fc["D"] == OPPOSITE[top]
            assert fc["B"] == OPPOSITE[front]
            valid += 1
    assert valid == 24  # the 24 cube orientations


def test_net_colors_follow_orientation():
    fc = face_colors("yellow", "green")  # flipped top/bottom vs default
    net = net_colors(S.SOLVED, fc)
    for face, cells in net.items():
        assert set(cells) == {fc[face]}
    assert net["U"][4] == "yellow"
    assert net["D"][4] == "white"
