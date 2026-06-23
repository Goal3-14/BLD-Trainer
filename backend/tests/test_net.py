from app.cube import state as S
from app.cube.net import net_colors
from app.cube.scramble import generate_scramble


def test_solved_net_is_uniform():
    net = net_colors(S.SOLVED)
    for face, cells in net.items():
        assert len(cells) == 9
        assert set(cells) == {S.FACE_COLORS[face]}  # whole face one color


def test_center_is_always_face_color():
    # Index 4 is the center cell (row 1, col 1); face moves never move centers.
    for seed in range(20):
        net = net_colors(S.scramble_state(generate_scramble(20, seed=seed)))
        for face, cells in net.items():
            assert cells[4] == S.FACE_COLORS[face]


def test_scramble_changes_some_stickers():
    net = net_colors(S.scramble_state(generate_scramble(20, seed=1)))
    # At least one face is no longer uniform.
    assert any(len(set(cells)) > 1 for cells in net.values())
