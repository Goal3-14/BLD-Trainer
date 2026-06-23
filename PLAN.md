# BLD Trainer — Overall Plan

A blindfolded-solving trainer focused on **memorization skills** (letter pairs + tracing) rather than physical execution. 3BLD first, built carefully as a reference implementation, with the architecture kept open for 4BLD/5BLD and an eventual cut-down Android client.

---

## 1. Goals & philosophy

- Drill the three skills that actually limit BLD memo: **letter recall**, **tracing**, and **combining the two under time**.
- Many small, swappable **practice modes** over one shared, correct core.
- **Correctness is non-negotiable.** The cube engine, tracer, and validator are unit-tested against hand-verified cases. A wrong tracing that "looks right" is the worst possible bug, so the core is the most-tested part of the app.
- **The UI is vital**, not an afterthought — the first milestone proves the engine *through* a real, usable UI, not headless.

### Non-goals (for now)
- Physical solve execution / move-by-move solver output.
- 4BLD/5BLD orbits (wings, centers, midges) — architecture stays open for them, but not built yet.
- The standalone algorithm/flashcard trainer (planned later phase).
- Mobile/tablet (a cut-down Android client may come later; PC is the reference).

---

## 2. Architecture

Two apps, one source of truth.

```
React + TypeScript frontend  <-- HTTP/JSON -->  Python (FastAPI) backend
   UI, modes, net rendering,                     cube engine, scheme, tracer,
   timers, input, local cache                    validator, scramble gen,
                                                  sheets/settings/stats storage
```

**Cube logic lives only in Python.** The frontend never re-implements cube math. For any cube operation it asks the backend, which returns plain data (e.g. a facelet color grid for the net, a list of target letters, a validation verdict).

**The API is stateless.** The backend does not hold "current scramble" session state. A scramble is just its move sequence; to validate a memo the frontend sends `{scramble moves, buffer/scheme/parity config, user's letter sequence}` and the backend recomputes everything from scratch and returns the verdict. This makes the backend trivial to reason about, test, and restart.

**Latency is a non-issue.** Validation happens once per *submission*, never per keystroke. Most no-scramble drills (letters↔words, image click) need no cube logic at all — they're pure data. So a local FastAPI round-trip is negligible.

---

## 3. Repository layout

```
bld-trainer/
  PLAN.md
  README.md
  backend/
    app/
      cube/
        state.py        # 48-sticker state model
        moves.py        # face-move permutation tables
        scramble.py     # scramble generation
        scheme.py       # Speffz + custom lettering schemes
        tracer.py       # state + buffers + conventions -> letter sequences
        validator.py    # letter sequence -> permutation -> solved? (the crux)
      models/           # Pydantic request/response + domain models
      storage/          # sheets / settings / stats persistence (JSON first)
      api/              # FastAPI routes
      main.py
    tests/              # pytest — heaviest coverage on tracer/validator
    pyproject.toml
  frontend/
    src/
      api/              # typed client (types generated from OpenAPI)
      cube/             # net renderer (SVG), shared TS types
      modes/            # mode framework + individual modes
      components/       # shared UI
      lib/              # timer, storage cache, helpers
      App.tsx
    package.json
    vite.config.ts
```

Single repo, two packages. During dev, Vite proxies `/api` to the FastAPI server (no CORS friction).

---

## 4. Tech stack

**Backend**
- Python 3.11+, **FastAPI** + **Uvicorn**, **Pydantic v2** for models/validation.
- **pytest** for tests.
- Storage: **JSON files** to start (human-editable, aligns naturally with sheet import/export). Move stats history to **SQLite** later if it grows.

**Frontend**
- **React + TypeScript + Vite**.
- **Vitest** + React Testing Library.
- Typed API client generated from FastAPI's OpenAPI schema (`openapi-typescript`) so DTOs can't drift between the two languages.
- Minimal state (React context / a small store); add a data-fetching lib only if needed.

**Dev workflow**
- `uvicorn` for the API, `vite` for the UI, run concurrently.
- Tests run on both sides; the Python core test suite is the gate for "is the engine correct."

---

## 5. Core domain design

### 5.1 State model
A 3×3 in a **fixed solving orientation** (default white top / green front; configurable later). Because BLD scrambles are face moves only (no rotations), the 6 centers never move, so we ignore them.

State = the **48 movable stickers** that Speffz already labels:
- 24 corner facelets (Speffz order, indices 0–23)
- 24 edge facelets (Speffz order, indices 0–23)

This is the key modeling choice: Speffz, tracing, and the net renderer all fall out of the same structure. Tracking *stickers* (not pieces) means in-place flips/twists are handled automatically — a flipped edge is simply a sticker permutation like any other.

### 5.2 Moves & scramble
- The 18 face moves (`U U' U2 D D' D2 L L' L2 R R' R2 F F' F2 B B' B2`) as precomputed permutations over the 48 stickers.
- Scramble generation: random face moves, length ~20–25, avoiding same-face and redundant opposite-face repeats.
- *Later:* WCA random-state (uniformly random) scrambles for realism.

### 5.3 Lettering scheme
- `scheme.py` maps each sticker index → a label. **Speffz is the default**, but the mapping is data, so custom schemes (rotated Speffz, numbers, fully custom) are supported. Letter-pair sheets are tied to a scheme.

### 5.4 Tracer (`tracer.py`)
Given a scrambled state, a chosen **corner buffer** and **edge buffer**, and a set of **conventions**, produce the corner and edge target-letter sequences — the memo.

Must handle, with conventions exposed as settings:
- **Cycle breaks** — when the buffer cycle closes with pieces still unsolved, break into a new cycle. *Which* sticker to break to is a configurable priority order.
- **Buffer solved at start** — break immediately.
- **In-place flipped edges / twisted corners** — fall out naturally from the sticker model.
- **Parity** — detect the odd-permutation case; report it so the validator/UI can apply the chosen parity strategy.

Output: `{corners: [letters], edges: [letters], hasParity: bool, solvedPieces: ...}` plus enough metadata for review/reconstruction.

### 5.5 Validator (`validator.py`) — **THE CRUX**
There is **no single correct memo** for a scramble (it depends on buffer, break choices, parity handling). So validation is **by simulation, not string-matching**:

> Reconstruct the permutation implied by the user's letter sequence (given their buffer/scheme/parity strategy) → apply it to the scrambled state → check whether the cube is solved.

This single function powers every tracing mode for every cube size and every buffer/parity config. The exact memo→permutation semantics (including parity and break conventions) is the highest-risk piece of the whole project and gets:
- a precise written spec,
- a dedicated test suite of hand-verified scrambles,
- a round-trip property test: `validate(trace(scramble)) == solved` for many random scrambles.

We build and lock this down **first**.

---

## 6. Data models

- **Scheme** — `{ id, name, cornerLabels[24], edgeLabels[24] }`.
- **PairEntry** — `{ pair: "AB", word: string, image?: url/ref, ideas: string[], notes?, tags?[], strength?: number }`. `ideas` is the alt-ideas list (click a pair → see them). `AB` and `BA` stored independently (optional "mirror" toggle).
- **Sheet** — `{ id, name, schemeId, entries: PairEntry[] }`. Import/export as plain CSV/JSON (and accept the CSV layout people already keep in spreadsheets).
- **Settings** — `{ cornerBuffer, edgeBuffer, schemeId, parityStrategy, breakConventions, cubeOrientation, ... }`.
- **AttemptResult** — `{ mode, timestamps (memo/recall split), correct, perTargetTiming?, scramble, userSequence, ... }` → feeds stats/SRS.

---

## 7. API surface (initial)

- `GET  /api/health`
- `POST /api/scramble` → `{ moves, facelets (net colors), scheme }`
- `POST /api/trace` → given scramble + buffers/scheme/conventions, return the target letters (used for review/answers, not for grading).
- `POST /api/validate` → given scramble + config + user letter sequence, return `{ solved, parity, firstDivergence?, ... }`.
- Sheets CRUD: `GET/POST/PUT/DELETE /api/sheets`, plus `/import` and `/export`.
- Settings: `GET/PUT /api/settings`.
- *(Later)* stats/attempts endpoints.

---

## 8. Frontend mode framework

Every mode is a small descriptor over the shared core, so adding one never touches the engine:

```ts
interface Mode {
  id: string;
  title: string;
  needsScramble: boolean;
  generatePrompt(ctx): Promise<Prompt>;   // may call backend (scramble) or be pure data
  inputKind: "letters" | "words" | "imageClick" | "pairs";
  validate(answer, prompt, ctx): Promise<Result>; // tracing modes -> backend /validate
  score(result): Score;
}
```

**Initial modes (Phase 1–2):**
1. *Type the letters* — scramble + net shown, validated by simulation. **(Phase 1 vertical slice.)**
2. Type the words for those letters (given the scheme/sheet).
3. No-scramble: given letters → type words.
4. No-scramble: given words → type letters.
5. Given letter pairs → click the image.
6. Given an image → type the pair / sequence of pairs.

**Scaling for "multi-like" memo:** modes that show content for a limited time then hide it and ask for recall, with a configurable number of items — this is how 3BLD drills stretch toward the load of 4/5BLD memo.

**Net renderer:** SVG component that takes the backend's facelet color grid and draws the standard unfolded net for scramble verification. Configurable color scheme; clickable-to-input a state is a later nice-to-have.

---

## 9. Settings that shape the engine

- **Corner buffer & edge buffer** — any valid sticker; ripples through tracer + validator.
- **Parity strategy** — full parity algorithm *or* your "swap 2 chosen edges" approach (configurable which 2). The validator honors the chosen strategy.
- **Cycle-break / new-cycle priority** convention.
- **Custom lettering scheme** selection.
- **Cube orientation** (default white top / green front).

---

## 10. Testing strategy

- **Engine:** apply known scrambles → assert known states; round-trip moves cancel.
- **Tracer:** hand-verified scrambles → expected target sequences (incl. cycle breaks, solved buffer, flipped/twisted, parity).
- **Validator:** the round-trip property (`validate(trace(x)) == solved`) over many random scrambles, plus deliberately wrong sequences → `not solved` with correct `firstDivergence`.
- **Frontend:** mode framework + net renderer unit tests; the API client is type-checked against the generated OpenAPI types.

---

## 11. Phased roadmap

- **Phase 0 — Scaffold.** Both apps, dev proxy, test runners, one end-to-end ping (frontend hits `/api/health`).
- **Phase 1 — Vertical slice (the most important bit + UI).** Cube engine + scheme + scramble + tracer + validator (Python, fully tested) → `/scramble` + `/validate` endpoints → SVG net renderer + *Type the letters* mode wired end-to-end → basic timer. Proves the core through a real UI.
- **Phase 2 — Modes & data.** Formalize the mode framework; add words↔letters and image modes; letter-pair lexicon model + in-app editor + import/export; settings (buffers, parity incl. 2-edge swap, custom scheme).
- **Phase 3 — Memo training depth.** Memo→hide→recall loops with split timing; stats + spaced-repetition weak-pair targeting; post-attempt reconstruction/review; optional audio (TTS) modes; session/playlist builder.
- **Phase 4 — Expansion.** 4BLD/5BLD orbit support (the simulation validator extends cheaply); standalone algorithm/flashcard trainer; eventual cut-down Android client.

---

## 12. Open questions / decisions to revisit

- Persistence: confirm JSON-files-first is fine, with SQLite reserved for stats history.
- Sheet import format: which existing spreadsheet/CSV layouts to accept on import.
- Default conventions (cycle-break priority) — pick sensible defaults, expose as settings.
- Whether `AB`/`BA` mirror by default or are always independent.
