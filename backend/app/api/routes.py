"""API routes: health, scheme, scramble, net, trace, validate."""
from fastapi import APIRouter

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
