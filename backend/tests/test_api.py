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
