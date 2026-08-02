"""Pydantic request/response models for the API."""
from __future__ import annotations

from pydantic import BaseModel, field_validator, model_validator

from app.cube import state as S
from app.cube.net import COLORS, OPPOSITE
from app.cube.scheme import LETTERS
from app.cube.tracer import DEFAULT_CORNER_BUFFER, DEFAULT_EDGE_BUFFER

_LETTERSET = set(LETTERS)


def _clean_letters(values: list[str]) -> list[str]:
    out: list[str] = []
    for v in values:
        u = v.strip().upper()
        if not u:
            continue
        if u not in _LETTERSET:
            raise ValueError(f"invalid Speffz letter: {v!r}")
        out.append(u)
    return out


def _validate_buffer(v: str) -> str:
    u = v.strip().upper()
    if u not in _LETTERSET:
        raise ValueError(f"invalid buffer letter: {v!r}")
    return u


def _validate_moves(moves: list[str]) -> list[str]:
    for m in moves:
        if m not in S.MOVES:
            raise ValueError(f"invalid move token: {m!r}")
    return moves


def _validate_color(v: str) -> str:
    c = v.strip().lower()
    if c not in COLORS:
        raise ValueError(f"unknown color: {v!r}")
    return c


class _Oriented(BaseModel):
    top_color: str = "white"
    front_color: str = "green"

    @field_validator("top_color", "front_color")
    @classmethod
    def _check_color(cls, v: str) -> str:
        return _validate_color(v)

    @model_validator(mode="after")
    def _check_orientation(self) -> "_Oriented":
        if self.top_color == self.front_color or OPPOSITE[self.top_color] == self.front_color:
            raise ValueError("top and front colors must be adjacent")
        return self


class ScrambleRequest(_Oriented):
    length: int = 20
    # Moves already on the cube. When set, the new scramble continues from that
    # state instead of from solved, so the solver need not reset between reps.
    prefix: list[str] = []
    corner_buffer: str = DEFAULT_CORNER_BUFFER
    edge_buffer: str = DEFAULT_EDGE_BUFFER

    @field_validator("length")
    @classmethod
    def _check_length(cls, v: int) -> int:
        if not 1 <= v <= 40:
            raise ValueError("length must be between 1 and 40")
        return v

    @field_validator("prefix")
    @classmethod
    def _check_prefix(cls, v: list[str]) -> list[str]:
        return _validate_moves(v)

    @field_validator("corner_buffer", "edge_buffer")
    @classmethod
    def _check_buffer(cls, v: str) -> str:
        return _validate_buffer(v)


class ScrambleResponse(BaseModel):
    scramble: list[str]  # the new moves to apply now
    full: list[str]  # prefix + scramble: the whole sequence from solved
    net: dict[str, list[str]]
    corner_buffer: str
    edge_buffer: str


class NetRequest(_Oriented):
    scramble: list[str]

    @field_validator("scramble")
    @classmethod
    def _check_moves(cls, v: list[str]) -> list[str]:
        return _validate_moves(v)


class NetResponse(BaseModel):
    net: dict[str, list[str]]


class TraceRequest(BaseModel):
    scramble: list[str]
    corner_buffer: str = DEFAULT_CORNER_BUFFER
    edge_buffer: str = DEFAULT_EDGE_BUFFER

    @field_validator("scramble")
    @classmethod
    def _check_moves(cls, v: list[str]) -> list[str]:
        return _validate_moves(v)

    @field_validator("corner_buffer", "edge_buffer")
    @classmethod
    def _check_buffer(cls, v: str) -> str:
        return _validate_buffer(v)


class TraceResponse(BaseModel):
    corners: list[str]
    edges: list[str]
    parity: bool


class ValidateRequest(BaseModel):
    scramble: list[str]
    corner_targets: list[str] = []
    edge_targets: list[str] = []
    corner_buffer: str = DEFAULT_CORNER_BUFFER
    edge_buffer: str = DEFAULT_EDGE_BUFFER

    @field_validator("scramble")
    @classmethod
    def _check_moves(cls, v: list[str]) -> list[str]:
        return _validate_moves(v)

    @field_validator("corner_targets", "edge_targets")
    @classmethod
    def _clean(cls, v: list[str]) -> list[str]:
        return _clean_letters(v)

    @field_validator("corner_buffer", "edge_buffer")
    @classmethod
    def _check_buffer(cls, v: str) -> str:
        return _validate_buffer(v)


class ValidateResponse(BaseModel):
    solved: bool
    corners_solved: bool
    edges_solved: bool


class LetterLabel(BaseModel):
    letter: str
    piece: str
    sticker: str


class SchemeResponse(BaseModel):
    corners: list[LetterLabel]
    edges: list[LetterLabel]
    colors: list[str]
