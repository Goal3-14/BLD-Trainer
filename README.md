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
