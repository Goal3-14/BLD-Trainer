"""API routes: health, scheme, scramble, net, trace, validate, images."""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from app import images as IMG
from app.cube import scheme as SC
from app.cube import state as S
from app.cube.net import COLORS, face_colors, net_colors
from app.cube.scramble import generate_scramble
from app.cube.tracer import trace_cube
from app.cube.validator import validate_cube
from app.models.schemas import (
    NetRequest,
    NetResponse,
    OrbitInfo,
    SchemeResponse,
    ScrambleRequest,
    ScrambleResponse,
    TraceRequest,
    TraceResponse,
    ValidateRequest,
    ValidateResponse,
)

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/scheme", response_model=SchemeResponse)
def get_scheme(size: int = 3) -> SchemeResponse:
    if size not in (3, 4, 5):
        raise HTTPException(status_code=400, detail="size must be 3, 4 or 5")
    cube = S.model(size)
    orbits = [
        OrbitInfo(
            kind=kind,
            title=orbit.title,
            default_buffer=orbit.default_buffer,
            labels=orbit.labels(cube),
        )
        for kind, orbit in SC.ORBITS[size].items()
    ]
    return SchemeResponse(
        size=size,
        orbits=orbits,
        colors=COLORS,
        corners=SC.corner_labels(),
        edges=SC.edge_labels(),
    )


@router.post("/scramble", response_model=ScrambleResponse)
def post_scramble(req: ScrambleRequest) -> ScrambleResponse:
    moves = generate_scramble(length=req.length, prefix=req.prefix, n=req.size)
    full = req.prefix + moves
    state = S.model(req.size).scramble_state(full)
    fc = face_colors(req.top_color, req.front_color)
    buffers = req.resolved_buffers()
    return ScrambleResponse(
        scramble=moves,
        full=full,
        net=net_colors(state, fc, req.size),
        size=req.size,
        buffers=buffers,
        corner_buffer=buffers.get("corner", req.corner_buffer),
        edge_buffer=buffers.get("edge", req.edge_buffer),
    )


@router.post("/net", response_model=NetResponse)
def post_net(req: NetRequest) -> NetResponse:
    state = S.model(req.size).scramble_state(req.scramble)
    fc = face_colors(req.top_color, req.front_color)
    return NetResponse(net=net_colors(state, fc, req.size), size=req.size)


@router.post("/trace", response_model=TraceResponse)
def post_trace(req: TraceRequest) -> TraceResponse:
    state = S.model(req.size).scramble_state(req.scramble)
    memo = trace_cube(state, req.size, req.resolved_buffers())
    return TraceResponse(
        targets=memo.targets,
        buffers=memo.buffers,
        parity=memo.parity,
        parity_by_orbit={k: memo.orbit_parity(k) for k in memo.targets},
        size=req.size,
        corners=memo.corners,
        edges=memo.edges,
    )


# --- Letter-pair images ------------------------------------------------------


def _check_pair(pair: str) -> str:
    p = pair.upper()
    if not IMG.PAIR_RE.match(p):
        raise HTTPException(status_code=400, detail="pair must be two letters A-X")
    return p


@router.get("/images")
def get_images() -> dict[str, dict[str, str]]:
    return {"images": IMG.list_images()}


@router.get("/images/{pair}")
def get_image(pair: str) -> FileResponse:
    path = IMG.find_image(_check_pair(pair))
    if path is None:
        raise HTTPException(status_code=404, detail="no image for this pair")
    ext = path.suffix.lower().lstrip(".")
    return FileResponse(path, media_type=IMG.MEDIA_TYPES[ext])


@router.put("/images/{pair}")
async def put_image(pair: str, request: Request, ext: str | None = None) -> dict[str, str]:
    p = _check_pair(pair)
    chosen = IMG.normalize_ext(ext, request.headers.get("content-type"))
    if chosen is None:
        raise HTTPException(status_code=415, detail="unsupported image type")
    data = await request.body()
    if not data:
        raise HTTPException(status_code=400, detail="empty body")
    if len(data) > IMG.MAX_BYTES:
        raise HTTPException(status_code=413, detail="image too large (10 MB max)")
    filename = IMG.save_image(p, data, chosen)
    return {"pair": p, "filename": filename}


@router.delete("/images/{pair}")
def del_image(pair: str) -> dict[str, bool]:
    return {"deleted": IMG.delete_image(_check_pair(pair))}


@router.post("/validate", response_model=ValidateResponse)
def post_validate(req: ValidateRequest) -> ValidateResponse:
    state = S.model(req.size).scramble_state(req.scramble)
    verdict = validate_cube(
        state, req.resolved_targets(), req.size, req.resolved_buffers()
    )
    return ValidateResponse(
        solved=verdict.solved,
        by_orbit=verdict.by_orbit,
        size=req.size,
        corners_solved=verdict.corners_solved,
        edges_solved=verdict.edges_solved,
    )
