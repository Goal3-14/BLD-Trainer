"""Lettering for wings, x-centres and t-centres on 4x4 and 5x5.

Anchors assert the piece a letter lands on, named the way a solver would say it
("A is UBR"), rather than restating the derivation. The wing anchors are the
ones that matter: chirality is the easy thing to get backwards, and UBR vs UBL
is exactly the difference between clockwise and anticlockwise.
"""
import pytest

from app.cube import scheme as SC
from app.cube import state as S


def _named(orbit, letter, n):
    """(piece name, sticker face) for a letter, e.g. ('UBR', 'U')."""
    fl = S.model(n).facelets[orbit.facelet_by_letter[letter]]
    return SC._piece_name(fl.pos), S.NORMAL_TO_FACE[fl.normal]


def _wing_name(letter, n):
    """A wing in solver notation: sticker face, the edge's other face, then the
    side it sits on — 'UBR' is the U sticker of the UB edge, on the R side."""
    cube = S.model(n)
    fl = cube.facelets[SC.ORBITS[n]["wing"].facelet_by_letter[letter]]
    face_axis = next(i for i in range(3) if fl.normal[i] != 0)
    partner_axis = next(
        i for i in range(3) if i != face_axis and abs(fl.pos[i]) == cube.outer
    )
    side_axis = next(i for i in range(3) if abs(fl.pos[i]) == cube.outer - 2)

    def face_at(axis: int, value: int) -> str:
        v = [0, 0, 0]
        v[axis] = 1 if value > 0 else -1
        return S.NORMAL_TO_FACE[tuple(v)]

    return (
        S.NORMAL_TO_FACE[fl.normal]
        + face_at(partner_axis, fl.pos[partner_axis])
        + face_at(side_axis, fl.pos[side_axis])
    )


@pytest.mark.parametrize("n", (4, 5))
def test_wing_anchors_are_the_clockwise_wing(n):
    # Clockwise round each face picks which of the two wings gets the letter.
    assert _wing_name("A", n) == "UBR"  # not UBL
    assert _wing_name("B", n) == "URF"
    assert _wing_name("M", n) == "RUB"
    assert _wing_name("Q", n) == "BUL"
    assert _wing_name("U", n) == "DFR"  # the usual wing buffer


@pytest.mark.parametrize("n", (4, 5))
def test_xcenter_anchors(n):
    centers = SC.ORBITS[n]["xcenter"]
    assert _named(centers, "A", n) == ("UBL", "U")  # the usual centre buffer
    assert _named(centers, "B", n) == ("UBR", "U")
    assert _named(centers, "U", n) == ("DFL", "D")


def test_tcenter_anchors():
    t = SC.ORBITS[5]["tcenter"]
    assert _named(t, "D", 5) == ("UL", "U")  # the usual edge-centre buffer
    assert _named(t, "A", 5) == ("UB", "U")
    assert _named(t, "U", 5) == ("DF", "D")


def test_midge_anchors_match_the_3x3_edge_scheme():
    """5x5 midges are the same piece class as 3x3 edges, so same letters."""
    midges = SC.ORBITS[5]["edge"]
    assert _named(midges, "A", 5) == ("UB", "U")
    assert _named(midges, "C", 5) == ("UF", "U")
    assert _named(midges, "U", 5) == ("DF", "D")


def test_which_orbits_exist_per_size():
    assert set(SC.ORBITS[3]) == {"corner", "edge"}
    assert set(SC.ORBITS[4]) == {"corner", "wing", "xcenter"}
    assert set(SC.ORBITS[5]) == {"corner", "edge", "wing", "xcenter", "tcenter"}


@pytest.mark.parametrize("n", (3, 4, 5))
def test_every_orbit_letters_24_distinct_stickers_of_its_own_kind(n):
    cube = S.model(n)
    for kind, orbit in SC.ORBITS[n].items():
        fids = list(orbit.facelet_by_letter.values())
        assert len(fids) == 24, (n, kind)
        assert len(set(fids)) == 24, (n, kind)
        assert set(fids) <= set(cube.ids_by_kind[kind]), (n, kind)
        for fid, letter in orbit.letter_by_facelet.items():
            assert orbit.facelet_by_letter[letter] == fid


@pytest.mark.parametrize("n", (4, 5))
def test_each_wing_slot_gets_exactly_one_lettered_sticker(n):
    """24 letters over 24 wing slots, one sticker each. Sound because a wing
    cannot flip, so its second sticker never needs naming."""
    cube = S.model(n)
    wings = SC.ORBITS[n]["wing"]
    slots = [cube.cubie_of[f] for f in wings.facelet_by_letter.values()]
    assert len(set(slots)) == 24
    assert set(slots) == set(cube.positions_by_kind["wing"])


@pytest.mark.parametrize("n", (4, 5))
def test_the_unlettered_wing_sticker_is_the_other_one(n):
    """Each wing has two stickers; exactly one carries a letter."""
    cube = S.model(n)
    lettered = set(SC.ORBITS[n]["wing"].facelet_by_letter.values())
    for pos in cube.positions_by_kind["wing"]:
        stickers = cube.facelets_at[pos]
        assert len(stickers) == 2
        assert len(lettered & set(stickers)) == 1


def test_3x3_tables_are_untouched():
    """The generalisation must not have moved any 3x3 letter."""
    assert SC.ORBITS[3]["corner"].facelet_by_letter == SC.CORNER_FACELET_BY_LETTER
    assert SC.ORBITS[3]["edge"].facelet_by_letter == SC.EDGE_FACELET_BY_LETTER


def test_default_buffers_are_the_conventional_stickers():
    o3, o4, o5 = SC.ORBITS[3], SC.ORBITS[4], SC.ORBITS[5]
    assert _named(o3["corner"], o3["corner"].default_buffer, 3) == ("UFR", "U")
    assert _named(o3["edge"], o3["edge"].default_buffer, 3) == ("UF", "U")
    assert _named(o4["corner"], o4["corner"].default_buffer, 4) == ("UFR", "U")
    assert _wing_name(o4["wing"].default_buffer, 4) == "DFR"
    assert _named(o4["xcenter"], o4["xcenter"].default_buffer, 4) == ("UBL", "U")
    assert _named(o5["edge"], o5["edge"].default_buffer, 5) == ("DF", "D")
    assert _named(o5["tcenter"], o5["tcenter"].default_buffer, 5) == ("UL", "U")


@pytest.mark.parametrize("n", (4, 5))
def test_wing_chirality_follows_the_move_generator(n):
    """The lettered wing sits where a clockwise turn of its face would carry the
    slot — the same rotation the move tables are built from."""
    cube = S.model(n)
    for letter, (face, cubie) in zip(SC.LETTERS, SC._EDGE_SPEFFZ):
        fid = SC.ORBITS[n]["wing"].facelet_by_letter[letter]
        pos = cube.facelets[fid].pos
        other = [c for c in cubie if c != face][0]
        axis, quarter = S.clockwise_quarter(face)
        cw = S.rotate(SC._DIR[other], axis, quarter)
        # The inner (off-centre) coordinate points along the clockwise direction.
        inner_axis = next(i for i in range(3) if abs(pos[i]) == cube.outer - 2)
        assert cw[inner_axis] != 0, letter
        assert (pos[inner_axis] > 0) == (cw[inner_axis] > 0), letter
