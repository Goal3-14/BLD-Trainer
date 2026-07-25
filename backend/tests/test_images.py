import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

PNG = b"\x89PNG\r\n\x1a\n fake image bytes"


@pytest.fixture(autouse=True)
def tmp_images_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("BLD_IMAGES_DIR", str(tmp_path))


def test_upload_list_get_delete_cycle():
    resp = client.put("/api/images/ab", content=PNG, headers={"content-type": "image/png"})
    assert resp.status_code == 200
    assert resp.json() == {"pair": "AB", "filename": "AB.png"}

    resp = client.get("/api/images")
    assert resp.json() == {"images": {"AB": "AB.png"}}

    resp = client.get("/api/images/AB")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert resp.content == PNG

    resp = client.delete("/api/images/AB")
    assert resp.json() == {"deleted": True}
    assert client.get("/api/images").json() == {"images": {}}
    assert client.get("/api/images/AB").status_code == 404


def test_reupload_replaces_old_extension():
    client.put("/api/images/CD", content=PNG, headers={"content-type": "image/png"})
    resp = client.put(
        "/api/images/CD?ext=jpeg", content=b"jpegdata", headers={"content-type": "image/jpeg"}
    )
    assert resp.json()["filename"] == "CD.jpeg"
    assert client.get("/api/images").json() == {"images": {"CD": "CD.jpeg"}}


def test_ext_hint_beats_content_type():
    resp = client.put(
        "/api/images/EF?ext=webp", content=b"data", headers={"content-type": "image/png"}
    )
    assert resp.json()["filename"] == "EF.webp"


def test_rejections():
    assert client.put("/api/images/ABC", content=PNG).status_code == 400
    assert client.put("/api/images/AZ", content=PNG).status_code == 400  # Z not in A-X
    assert (
        client.put("/api/images/AB", content=PNG, headers={"content-type": "text/plain"}).status_code
        == 415
    )
    assert (
        client.put("/api/images/AB", content=b"", headers={"content-type": "image/png"}).status_code
        == 400
    )
    assert client.get("/api/images/QX").status_code == 404
