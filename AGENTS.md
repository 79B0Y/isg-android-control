# Repository Guidelines

## Project Structure & Module Organization
- `src/`: FastAPI service, CLI entry (`src/main.py`), core logic under `core/`, routes under `api/routes/`, MQTT in `mqtt/`, services in `services/`.
- `configs/`: Runtime config (`config.yaml`).
- `data/`: Logs and screenshots (`data/logs`, `data/screenshots`).
- `tests/`: Place unit/integration tests (`tests/unit`, `tests/integration`).
- Scripts: installer and helpers (`install.sh`, `install-mac.sh`, `install-termux-ubuntu.sh`, `connect*.sh`, `start*.sh`, `stop*.sh`).
- CLI: `./isg-android-control` wrapper; Python entrypoint `android-control` maps to `src.main:main`.

## Build, Test, and Development Commands
- Setup: `python3 -m venv venv && source venv/bin/activate && pip install -e .[dev]`
- Run (daemon): `./isg-android-control start` (uses `configs/config.yaml`).
- Run (dev): `android-control --reload -c configs/config.yaml -p 8000`
- API docs: visit `http://localhost:8000/docs`.
- Tests: `pytest -q` or `pytest --cov=src`.
- Lint/Format: `black . && isort . && flake8 src tests && mypy src`

## Coding Style & Naming Conventions
- Python 3.9+; 4-space indent; max line length 88 (Black).
- Use type hints; modules/functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.
- Keep FastAPI routers in `api/routes/*` and business logic in `core/` or `services/` (avoid heavy logic in route handlers).

## Testing Guidelines
- Framework: pytest (+ pytest-asyncio for async endpoints).
- Place tests under `tests/unit` or `tests/integration`; name files `test_*.py`.
- API tests: use `httpx.AsyncClient` against the FastAPI app factory `src.main:create_application`.
- CLI smoke: see `test_cli.py` for examples; prefer idempotent checks and avoid starting real services in unit tests.

## Commit & Pull Request Guidelines
- Commits in this repo are short and imperative (e.g., "update logger"). Prefer clear, scoped messages; Conventional Commits are welcome (e.g., `feat(core): add ADB retry`).
- PRs should include: purpose, summary of changes, manual test steps, related issues (e.g., `Closes #123`), and config impacts (`.env`, `configs/config.yaml`). Add logs/screenshots when relevant.

## Security & Configuration Tips
- Do not commit secrets; use `.env` (see `.env.example`).
- Keep MQTT/ADB endpoints in `configs/config.yaml`; verify before running.
- Logs write to `data/logs`; avoid sensitive payloads in logs.
