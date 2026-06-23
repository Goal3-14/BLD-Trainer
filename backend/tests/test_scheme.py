"""Speffz scheme correctness.

Anchor tests assert real geometry/colors for well-known stickers (not the table
restated), so a pass means the derivation genuinely matches standard Speffz.
"""
from app.cube import scheme as SC
from app.cube import state as S

_DIR = SC._DIR


def _pos(cubie):
    return (
        sum(_DIR[c][0] for c in cubie),
        sum(_DIR[c][1] for c in cubie),
        sum(_DIR[c][2] for c in cubie),
    )


def test_24_distinct_corner_and_edge_facelets():
    assert len(SC.LETTERS) == 24
    cf = list(SC.CORNER_FACELET_BY_LETTER.values())
    ef = list(SC.EDGE_FACELET_BY_LETTER.values())
    assert len(set(cf)) == 24 and set(cf) == set(S.CORNER_IDS)
    assert len(set(ef)) == 24 and set(ef) == set(S.EDGE_IDS)


def test_letter_facelet_roundtrip():
    for letter, fid in SC.CORNER_FACELET_BY_LETTER.items():
        assert SC.CORNER_LETTER_BY_FACELET[fid] == letter
    for letter, fid in SC.EDGE_FACELET_BY_LETTER.items():
        assert SC.EDGE_LETTER_BY_FACELET[fid] == letter


def _corner(letter):
    return S.FACELETS[SC.CORNER_FACELET_BY_LETTER[letter]]

def _edge(letter):
    return S.FACELETS[SC.EDGE_FACELET_BY_LETTER[letter]]


def test_corner_anchors():
    # A = U-sticker of UBL (white)
    a = _corner("A")
    assert a.pos == _pos("UBL") and a.normal == _DIR["U"] and a.color == "white"
    # E = L-sticker of UBL (orange) -- first letter of the L block
    e = _corner("E")
    assert e.pos == _pos("UBL") and e.normal == _DIR["L"] and e.color == "orange"
    # I = F-sticker of UFL (green) -- first letter of the F block
    i = _corner("I")
    assert i.pos == _pos("UFL") and i.normal == _DIR["F"] and i.color == "green"
    # U = D-sticker of DFL (yellow) -- first letter of the D block (x2 rule)
    u = _corner("U")
    assert u.pos == _pos("DFL") and u.normal == _DIR["D"] and u.color == "yellow"


def test_edge_anchors():
    # A = U-sticker of UB (white)
    a = _edge("A")
    assert a.pos == _pos("UB") and a.normal == _DIR["U"] and a.color == "white"
    # C = U-sticker of UF (white)
    c = _edge("C")
    assert c.pos == _pos("UF") and c.normal == _DIR["U"] and c.color == "white"
    # U = D-sticker of DF (yellow) -- the classic M2 buffer sticker
    u = _edge("U")
    assert u.pos == _pos("DF") and u.normal == _DIR["D"] and u.color == "yellow"


def test_each_face_block_shares_a_normal():
    # Letters group into 6 blocks of 4, each block on one face (U,L,F,R,B,D order).
    faces = ["U", "L", "F", "R", "B", "D"]
    for block, face in enumerate(faces):
        for k in range(4):
            letter = SC.LETTERS[block * 4 + k]
            assert _corner(letter).normal == _DIR[face]
            assert _edge(letter).normal == _DIR[face]


def test_ubl_corner_has_letters_A_E_R():
    # The three stickers of the UBL corner are A (U), E (L), R (B).
    letters_at_ubl = {
        L for L, fid in SC.CORNER_FACELET_BY_LETTER.items()
        if S.FACELETS[fid].pos == _pos("UBL")
    }
    assert letters_at_ubl == {"A", "E", "R"}
