"""Pydantic request/response models for the API.

Every request carries a cube ``size`` (3, 4 or 5), defaulting to 3 so existing
3x3 callers are unchanged. Memos are keyed by orbit — "corner", "edge", "wing",
"xcenter", "tcenter" — because which orbits exist depends on the size. The 3x3
``corner_``/``edge_`` fields are kept as a view onto the same data.
"""
from __future__ import annotations

from pydantic import BaseModel, field_validator, model_validator

from app.cube import scheme as SC
from app.cube import state as S
from app.cube.net import COLORS, OPPOSITE
from app.cube.scheme import LETTERS
from app.cube.tracer import DEFAULT_CORNER_BUFFER, DEFAULT_EDGE_BUFFER

_LETTERSET = set(LETTERS)
SIZES = (3, 4, 5)


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


def _validate_color(v: str) -> str:
    c = v.strip().lower()
    if c not in COLORS:
        raise ValueError(f"unknown color: {v!r}")
    return c


class _Sized(BaseModel):
    size: int = 3

    @field_validator("size")
    @classmethod
    def _check_size(cls, v: int) -> int:
        if v not in SIZES:
            raise ValueError(f"size must be one of {SIZES}")
        return v

    def check_moves(self, moves: list[str]) -> list[str]:
        """Move tokens are only meaningful against a size, so this runs after
        the whole model is built rather than as a field validator."""
        legal = S.model(self.size).MOVES
        for m in moves:
            if m not in legal:
                raise ValueError(f"invalid move token for {self.size}x{self.size}: {m!r}")
        return moves

    def check_buffers(self, buffers: dict[str, str]) -> dict[str, str]:
        orbits = SC.ORBITS[self.size]
        out: dict[str, str] = {}
        for kind, letter in buffers.items():
            if kind not in orbits:
                raise ValueError(f"{self.size}x{self.size} has no {kind!r} orbit")
            out[kind] = _validate_buffer(letter)
        return out


class _Oriented(_Sized):
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
    # None means "the usual length for this size" (20 / 40 / 60).
    length: int | None = None
    # Moves already on the cube. When set, the new scramble continues from that
    # state instead of from solved, so the solver need not reset between reps.
    prefix: list[str] = []
    buffers: dict[str, str] = {}
    corner_buffer: str = DEFAULT_CORNER_BUFFER
    edge_buffer: str = DEFAULT_EDGE_BUFFER

    @field_validator("length")
    @classmethod
    def _check_length(cls, v: int | None) -> int | None:
        if v is not None and not 1 <= v <= 100:
            raise ValueError("length must be between 1 and 100")
        return v

    @field_validator("corner_buffer", "edge_buffer")
    @classmethod
    def _check_buffer(cls, v: str) -> str:
        return _validate_buffer(v)

    @model_validator(mode="after")
    def _check(self) -> "ScrambleRequest":
        self.check_moves(self.prefix)
        self.buffers = self.check_buffers(self.buffers)
        return self

    def resolved_buffers(self) -> dict[str, str]:
        """Every orbit's buffer: the request's overrides over the defaults."""
        out = {k: o.default_buffer for k, o in SC.ORBITS[self.size].items()}
        if self.size == 3:
            out["corner"] = self.corner_buffer
            out["edge"] = self.edge_buffer
        out.update(self.buffers)
        return out


class ScrambleResponse(BaseModel):
    scramble: list[str]  # the new moves to apply now
    full: list[str]  # prefix + scramble: the whole sequence from solved
    net: dict[str, list[str]]
    size: int
    buffers: dict[str, str]
    corner_buffer: str
    edge_buffer: str


class NetRequest(_Oriented):
    scramble: list[str]

    @model_validator(mode="after")
    def _check(self) -> "NetRequest":
        self.check_moves(self.scramble)
        return self


class NetResponse(BaseModel):
    net: dict[str, list[str]]
    size: int


class TraceRequest(_Sized):
    scramble: list[str]
    buffers: dict[str, str] = {}
    corner_buffer: str = DEFAULT_CORNER_BUFFER
    edge_buffer: str = DEFAULT_EDGE_BUFFER

    @field_validator("corner_buffer", "edge_buffer")
    @classmethod
    def _check_buffer(cls, v: str) -> str:
        return _validate_buffer(v)

    @model_validator(mode="after")
    def _check(self) -> "TraceRequest":
        self.check_moves(self.scramble)
        self.buffers = self.check_buffers(self.buffers)
        return self

    def resolved_buffers(self) -> dict[str, str]:
        """Orbit buffers, with the 3x3 corner_/edge_ fields folded in."""
        out = dict(self.buffers)
        if self.size == 3:
            out.setdefault("corner", self.corner_buffer)
            out.setdefault("edge", self.edge_buffer)
        return out


class TraceResponse(BaseModel):
    targets: dict[str, list[str]]
    buffers: dict[str, str]
    parity: bool
    parity_by_orbit: dict[str, bool]
    size: int
    corners: list[str]
    edges: list[str]


class ValidateRequest(_Sized):
    scramble: list[str]
    targets: dict[str, list[str]] = {}
    corner_targets: list[str] = []
    edge_targets: list[str] = []
    buffers: dict[str, str] = {}
    corner_buffer: str = DEFAULT_CORNER_BUFFER
    edge_buffer: str = DEFAULT_EDGE_BUFFER

    @field_validator("corner_targets", "edge_targets")
    @classmethod
    def _clean(cls, v: list[str]) -> list[str]:
        return _clean_letters(v)

    @field_validator("corner_buffer", "edge_buffer")
    @classmethod
    def _check_buffer(cls, v: str) -> str:
        return _validate_buffer(v)

    @model_validator(mode="after")
    def _check(self) -> "ValidateRequest":
        self.check_moves(self.scramble)
        self.buffers = self.check_buffers(self.buffers)
        orbits = SC.ORBITS[self.size]
        cleaned: dict[str, list[str]] = {}
        for kind, letters in self.targets.items():
            if kind not in orbits:
                raise ValueError(f"{self.size}x{self.size} has no {kind!r} orbit")
            cleaned[kind] = _clean_letters(letters)
        self.targets = cleaned
        return self

    def resolved_targets(self) -> dict[str, list[str]]:
        out = dict(self.targets)
        if self.size == 3:
            out.setdefault("corner", self.corner_targets)
            out.setdefault("edge", self.edge_targets)
        return out

    def resolved_buffers(self) -> dict[str, str]:
        out = dict(self.buffers)
        if self.size == 3:
            out.setdefault("corner", self.corner_buffer)
            out.setdefault("edge", self.edge_buffer)
        return out


class ValidateResponse(BaseModel):
    solved: bool
    by_orbit: dict[str, bool]
    size: int
    corners_solved: bool
    edges_solved: bool


class LetterLabel(BaseModel):
    letter: str
    piece: str
    sticker: str


class OrbitInfo(BaseModel):
    kind: str
    title: str
    default_buffer: str
    labels: list[LetterLabel]


class SchemeResponse(BaseModel):
    size: int
    orbits: list[OrbitInfo]
    colors: list[str]
    corners: list[LetterLabel]
    edges: list[LetterLabel]
