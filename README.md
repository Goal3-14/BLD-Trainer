# BLD Trainer

A blindfolded-solving trainer focused on memorization skills (letter pairs + tracing).
3BLD first. See [PLAN.md](PLAN.md) for the full design.

## Structure

- `backend/` — Python + FastAPI. Cube engine, tracer, validator, API. The single source of truth for all cube logic.
- `frontend/` — React + TypeScript + Vite. UI, practice modes, net rendering.

## Development

### Backend

```sh
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Windows
.venv/Scripts/python -m uvicorn app.main:app --reload      # run API on :8000
.venv/Scripts/python -m pytest                             # run tests
```

### Frontend

```sh
cd frontend
npm install
npm run dev        # Vite dev server, proxies /api to the backend
```

## Phone app (GitHub Pages)

A cut-down build for the phone: the letter-pair drills only — no cube, no
scrambles, no images — so it needs no backend and works offline.

```sh
cd frontend
npm run build:pages   # -> dist/, installable, served from /BLD-Trainer/
```

Pushing to `main` builds and publishes it automatically via
[.github/workflows/deploy-pages.yml](.github/workflows/deploy-pages.yml). One-time
setup: **Settings → Pages → Source: GitHub Actions**. Publishing from a private
repo needs a paid GitHub plan; on the free plan the repo must be public.

Then open the published link on the phone and use Chrome's **Add to Home
Screen**. Your pair list is not part of the build — paste it in once from the
desktop app's CSV export, under the **Letter-Pair Sheet** tab. It is saved on
the device and stays there.
