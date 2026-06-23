"""Pydantic request/response models for the API."""
from __future__ import annotations

from pydantic import BaseModel, field_validator

from app.cube import state as S
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


class ScrambleRequest(BaseModel):
    length: int = 20
    corner_buffer: str = DEFAULT_CORNER_BUFFER
    edge_buffer: str = DEFAULT_EDGE_BUFFER

    @field_validator("length")
    @classmethod
    def _check_length(cls, v: int) -> int:
        if not 1 <= v <= 40:
            raise ValueError("length must be between 1 and 40")
        return v

    @field_validator("corner_buffer", "edge_buffer")
    @classmethod
    def _check_buffer(cls, v: str) -> str:
        return _validate_buffer(v)


class ScrambleResponse(BaseModel):
    scramble: list[str]
    net: dict[str, list[str]]
    corner_buffer: str
    edge_buffer: str


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
