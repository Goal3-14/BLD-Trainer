"""API routes: health, scheme, scramble, net, trace, validate, images."""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from app import images as IMG
from app.cube import scheme as SC
from app.cube import state as S
from app.cube.net import COLORS, face_colors, net_colors
from app.cube.scramble import generate_scramble
from app.cube.tracer import trace
from app.cube.validator import validate as validate_memo
from app.models.schemas import (
    NetRequest,
    NetResponse,
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
def get_scheme() -> SchemeResponse:
    return SchemeResponse(
        corners=SC.corner_labels(),
        edges=SC.edge_labels(),
        colors=COLORS,
    )


@router.post("/scramble", response_model=ScrambleResponse)
def post_scramble(req: ScrambleRequest) -> ScrambleResponse:
    moves = generate_scramble(length=req.length)
    state = S.scramble_state(moves)
    fc = face_colors(req.top_color, req.front_color)
    return ScrambleResponse(
        scramble=moves,
        net=net_colors(state, fc),
        corner_buffer=req.corner_buffer,
        edge_buffer=req.edge_buffer,
    )


@router.post("/net", response_model=NetResponse)
def post_net(req: NetRequest) -> NetResponse:
    state = S.scramble_state(req.scramble)
    fc = face_colors(req.top_color, req.front_color)
    return NetResponse(net=net_colors(state, fc))


@router.post("/trace", response_model=TraceResponse)
def post_trace(req: TraceRequest) -> TraceResponse:
    state = S.scramble_state(req.scramble)
    memo = trace(state, req.corner_buffer, req.edge_buffer)
    return TraceResponse(corners=memo.corners, edges=memo.edges, parity=memo.parity)


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
    state = S.scramble_state(req.scramble)
    verdict = validate_memo(
        state, req.corner_targets, req.edge_targets, req.corner_buffer, req.edge_buffer
    )
    return ValidateResponse(
        solved=verdict.solved,
        corners_solved=verdict.corners_solved,
        edges_solved=verdict.edges_solved,
    )
