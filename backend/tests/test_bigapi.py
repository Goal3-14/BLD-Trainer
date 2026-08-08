"""The API over 4x4 and 5x5. `size` defaults to 3, so 3x3 callers see no change."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.parametrize("size,length", [(3, 20), (4, 40), (5, 60)])
def test_scramble_defaults_to_the_usual_length(size, length):
    body = client.post("/api/scramble", json={"size": size}).json()
    assert len(body["scramble"]) == length
    assert body["size"] == size
    assert body["full"] == body["scramble"]


@pytest.mark.parametrize("size", [3, 4, 5])
def test_net_has_a_cell_per_sticker(size):
    body = client.post("/api/scramble", json={"size": size}).json()
    assert set(body["net"]) == {"U", "L", "F", "R", "B", "D"}
    for cells in body["net"].values():
        assert len(cells) == size * size


@pytest.mark.parametrize("size,orbits", [
    (3, {"corner", "edge"}),
    (4, {"corner", "wing", "xcenter"}),
    (5, {"corner", "edge", "wing", "xcenter", "tcenter"}),
])
def test_trace_returns_every_orbit_of_that_size(size, orbits):
    scr = client.post("/api/scramble", json={"size": size}).json()["full"]
    tr = client.post("/api/trace", json={"scramble": scr, "size": size}).json()
    assert set(tr["targets"]) == orbits
    assert set(tr["buffers"]) == orbits
    assert set(tr["parity_by_orbit"]) == orbits


@pytest.mark.parametrize("size", [3, 4, 5])
def test_full_roundtrip_scramble_trace_validate(size):
    scr = client.post("/api/scramble", json={"size": size}).json()["full"]
    tr = client.post("/api/trace", json={"scramble": scr, "size": size}).json()
    v = client.post("/api/validate", json={
        "scramble": scr, "size": size,
        "targets": tr["targets"], "buffers": tr["buffers"],
    }).json()
    assert v["solved"] is True
    assert all(v["by_orbit"].values())


@pytest.mark.parametrize("size", [4, 5])
def test_dropping_one_target_fails_that_orbit(size):
    scr = client.post("/api/scramble", json={"size": size}).json()["full"]
    tr = client.post("/api/trace", json={"scramble": scr, "size": size}).json()
    targets = dict(tr["targets"])
    targets["xcenter"] = targets["xcenter"][:-1]
    v = client.post("/api/validate", json={
        "scramble": scr, "size": size, "targets": targets, "buffers": tr["buffers"],
    }).json()
    assert v["solved"] is False
    assert v["by_orbit"]["xcenter"] is False


def test_default_buffers_are_reported():
    body = client.post("/api/scramble", json={"size": 4}).json()
    assert body["buffers"] == {"corner": "C", "wing": "U", "xcenter": "A"}
    body5 = client.post("/api/scramble", json={"size": 5}).json()
    assert body5["buffers"]["edge"] == "U" and body5["buffers"]["tcenter"] == "D"


def test_buffers_can_be_overridden_per_orbit():
    scr = client.post("/api/scramble", json={"size": 4}).json()["full"]
    tr = client.post("/api/trace", json={
        "scramble": scr, "size": 4, "buffers": {"wing": "A", "xcenter": "X"},
    }).json()
    assert tr["buffers"]["wing"] == "A" and tr["buffers"]["xcenter"] == "X"
    v = client.post("/api/validate", json={
        "scramble": scr, "size": 4, "targets": tr["targets"], "buffers": tr["buffers"],
    }).json()
    assert v["solved"] is True  # a different buffer is still a valid memo


def test_scheme_describes_each_orbit():
    body = client.get("/api/scheme", params={"size": 4}).json()
    assert body["size"] == 4
    kinds = {o["kind"]: o for o in body["orbits"]}
    assert set(kinds) == {"corner", "wing", "xcenter"}
    assert kinds["wing"]["title"] == "Wings"
    assert kinds["xcenter"]["default_buffer"] == "A"
    for orbit in body["orbits"]:
        assert len(orbit["labels"]) == 24
    # A is the clockwise wing of the UB edge.
    wing_a = next(l for l in kinds["wing"]["labels"] if l["letter"] == "A")
    assert wing_a["sticker"] == "U"


def test_scheme_still_serves_the_3x3_shape():
    body = client.get("/api/scheme").json()
    assert body["size"] == 3
    assert len(body["corners"]) == 24 and len(body["edges"]) == 24


# --- rejections --------------------------------------------------------------


def test_unknown_size_is_rejected():
    assert client.post("/api/scramble", json={"size": 6}).status_code == 422
    assert client.get("/api/scheme", params={"size": 2}).status_code == 400


def test_wide_move_rejected_on_3x3():
    r = client.post("/api/trace", json={"scramble": ["Rw"], "size": 3})
    assert r.status_code == 422


def test_wide_move_accepted_on_4x4():
    r = client.post("/api/trace", json={"scramble": ["Rw", "Uw2", "Lw'"], "size": 4})
    assert r.status_code == 200


def test_orbit_that_does_not_exist_is_rejected():
    scr = client.post("/api/scramble", json={"size": 4}).json()["full"]
    r = client.post("/api/validate", json={
        "scramble": scr, "size": 4, "targets": {"tcenter": ["A"]},
    })
    assert r.status_code == 422  # 4x4 has no edge centres
    r2 = client.post("/api/trace", json={
        "scramble": scr, "size": 4, "buffers": {"edge": "C"},
    })
    assert r2.status_code == 422  # nor midges


def test_continuing_a_4x4_scramble():
    first = client.post("/api/scramble", json={"size": 4}).json()
    second = client.post("/api/scramble", json={"size": 4, "prefix": first["full"]}).json()
    assert len(second["scramble"]) == 40
    assert second["full"] == first["full"] + second["scramble"]
    net = client.post("/api/net", json={"scramble": second["full"], "size": 4}).json()
    assert second["net"] == net["net"] and net["size"] == 4
