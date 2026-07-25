"""Letter-pair image store.

Images live in a plain folder (backend/data/images by default, override with
the BLD_IMAGES_DIR env var) named after the pair they belong to: AB.png,
AD.jpeg, GH.webp... One image per pair; uploading replaces any previous file
regardless of extension.
"""
import os
import re
from pathlib import Path

PAIR_RE = re.compile(r"^[A-X]{2}$")

# Extension -> media type. Doubles as the allowlist for uploads.
MEDIA_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
    "avif": "image/avif",
    "bmp": "image/bmp",
}

MAX_BYTES = 10 * 1024 * 1024

_DEFAULT_DIR = Path(__file__).resolve().parent.parent / "data" / "images"


def images_dir() -> Path:
    d = Path(os.environ.get("BLD_IMAGES_DIR", _DEFAULT_DIR))
    d.mkdir(parents=True, exist_ok=True)
    return d


def normalize_ext(ext: str | None, content_type: str | None) -> str | None:
    """Pick a file extension from an explicit hint or the request content type."""
    if ext:
        e = ext.lower().lstrip(".")
        if e in MEDIA_TYPES:
            return e
    if content_type:
        ct = content_type.split(";")[0].strip().lower()
        for e, mt in MEDIA_TYPES.items():
            if mt == ct:
                return e
    return None


def find_image(pair: str) -> Path | None:
    for ext in MEDIA_TYPES:
        p = images_dir() / f"{pair}.{ext}"
        if p.is_file():
            return p
    return None


def list_images() -> dict[str, str]:
    """Map of pair -> filename for every stored image."""
    out: dict[str, str] = {}
    for p in sorted(images_dir().iterdir()):
        ext = p.suffix.lower().lstrip(".")
        if p.is_file() and ext in MEDIA_TYPES and PAIR_RE.match(p.stem):
            out[p.stem] = p.name
    return out


def save_image(pair: str, data: bytes, ext: str) -> str:
    delete_image(pair)
    path = images_dir() / f"{pair}.{ext}"
    path.write_bytes(data)
    return path.name


def delete_image(pair: str) -> bool:
    found = False
    for ext in MEDIA_TYPES:
        p = images_dir() / f"{pair}.{ext}"
        if p.is_file():
            p.unlink()
            found = True
    return found
