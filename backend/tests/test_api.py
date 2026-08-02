from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_scramble_shape():
    r = client.post("/api/scramble", json={"length": 20})
    assert r.status_code == 200
    body = r.json()
    assert len(body["scramble"]) == 20
    assert set(body["net"]) == {"U", "L", "F", "R", "B", "D"}
    for face, cells in body["net"].items():
        assert len(cells) == 9
    assert body["corner_buffer"] and body["edge_buffer"]
    assert body["full"] == body["scramble"]  # no prefix -> full sequence is the scramble


def test_scramble_with_prefix_continues_from_that_state():
    first = client.post("/api/scramble", json={"length": 20}).json()
    second = client.post(
        "/api/scramble", json={"length": 20, "prefix": first["full"]}
    ).json()
    assert len(second["scramble"]) == 20  # only the new moves to apply
    assert second["full"] == first["full"] + second["scramble"]
    # The net must show the continued state, not a fresh 20-move scramble.
    net = client.post("/api/net", json={"scramble": second["full"]}).json()["net"]
    assert second["net"] == net


def test_continued_scramble_roundtrips():
    # A chain of "next scramble" reps must stay traceable/validatable throughout.
    full: list[str] = []
    for _ in range(4):
        full = client.post("/api/scramble", json={"length": 20, "prefix": full}).json()["full"]
        tr = client.post("/api/trace", json={"scramble": full}).json()
        v = client.post(
            "/api/validate",
            json={"scramble": full, "corner_targets": tr["corners"], "edge_targets": tr["edges"]},
        ).json()
        assert v["solved"] is True


def test_scramble_rejects_a_bad_prefix():
    r = client.post("/api/scramble", json={"length": 20, "prefix": ["R", "nope"]})
    assert r.status_code == 422


def test_full_api_roundtrip():
    # scramble -> trace -> validate should report solved, regardless of randomness.
    scr = client.post("/api/scramble", json={"length": 20}).json()["scramble"]
    tr = client.post("/api/trace", json={"scramble": scr}).json()
    v = client.post(
        "/api/validate",
        json={"scramble": scr, "corner_targets": tr["corners"], "edge_targets": tr["edges"]},
    ).json()
    assert v["solved"] is True


def test_validate_empty_is_unsolved():
    scr = client.post("/api/scramble", json={"length": 20}).json()["scramble"]
    v = client.post("/api/validate", json={"scramble": scr}).json()
    assert v["solved"] is False


def test_validate_rejects_bad_letter():
    scr = client.post("/api/scramble", json={"length": 20}).json()["scramble"]
    r = client.post("/api/validate", json={"scramble": scr, "corner_targets": ["Z"]})
    assert r.status_code == 422


def test_validate_rejects_bad_move():
    r = client.post("/api/validate", json={"scramble": ["R", "bogus"]})
    assert r.status_code == 422


def test_lowercase_letters_accepted():
    scr = client.post("/api/scramble", json={"length": 20}).json()["scramble"]
    tr = client.post("/api/trace", json={"scramble": scr}).json()
    lower = {
        "scramble": scr,
        "corner_targets": [c.lower() for c in tr["corners"]],
        "edge_targets": [e.lower() for e in tr["edges"]],
    }
    assert client.post("/api/validate", json=lower).json()["solved"] is True


def test_scheme_endpoint():
    s = client.get("/api/scheme").json()
    assert len(s["corners"]) == 24 and len(s["edges"]) == 24
    assert set(s["colors"]) == {"white", "yellow", "green", "blue", "red", "orange"}
    a = next(c for c in s["corners"] if c["letter"] == "A")
    assert a["piece"] == "UBL" and a["sticker"] == "U"
    eu = next(e for e in s["edges"] if e["letter"] == "U")
    assert eu["piece"] == "DF" and eu["sticker"] == "D"


def test_scramble_with_orientation():
    r = client.post("/api/scramble", json={"length": 20, "top_color": "yellow", "front_color": "green"})
    assert r.status_code == 200
    assert r.json()["net"]["U"][4] == "yellow"  # U center recolored


def test_invalid_orientation_rejected():
    r = client.post("/api/scramble", json={"top_color": "white", "front_color": "yellow"})
    assert r.status_code == 422  # opposite colors are not a valid orientation


def test_net_endpoint_recolors():
    scr = client.post("/api/scramble", json={"length": 20}).json()["scramble"]
    n = client.post("/api/net", json={"scramble": scr, "top_color": "yellow", "front_color": "green"}).json()
    assert n["net"]["U"][4] == "yellow"
    assert set(n["net"]) == {"U", "L", "F", "R", "B", "D"}
