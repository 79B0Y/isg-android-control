# Repository Guidelines

This repository contains a Home Assistant custom integration for controlling Android TV boxes via ADB, plus a lightweight web interface for status and actions.

## Project Structure & Module Organization
- `custom_components/android_tv_box/`: Integration code
  - `__init__.py`, `config.py`, `config_flow.py`: setup and config flow
  - `media_player.py`, `switch.py`, `camera.py`, `sensor.py`, `remote.py`, `select.py`, `binary_sensor.py`
  - `adb_service.py`, `services.py`, `web_server.py`, `web/` (HTML/CSS/JS)
- Test scripts: `test_*.py` in repo root (integration and ADB checks)
- Scripts: `deploy.sh` (copy to HA), `release.sh` (HACS validation), `setup_ubuntu.sh`, `setup_android.sh`

## Build, Test, and Development Commands
- Create env and install deps:
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt`
- Run quick checks (examples):
  - `python test_adb_connection.py` (verify ADB)
  - `python test_integration.py` (HA API + web UI)
  - `python test_all_functions.py` (broader feature pass)
- Validate packaging: `bash release.sh`
- Deploy locally to HA: `bash deploy.sh` (copies to `.../custom_components/` and appends config)

## Coding Style & Naming Conventions
- Python, PEP 8, 4‑space indentation; add type hints and docstrings.
- Names: `snake_case` for functions/vars/files, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Follow Home Assistant patterns (ConfigEntry, `DataUpdateCoordinator`, async I/O).

## Testing Guidelines
- Prefer runnable scripts under repo root named `test_*.py` with clear output.
- Validate on a real device or emulator with ADB enabled.
- For web server checks, ensure port `3003` is reachable: `curl http://localhost:3003`.
- Keep tests idempotent and avoid destructive device actions by default.

## Commit & Pull Request Guidelines
- Commit messages: conventional style (e.g., `feat:`, `fix:`, `docs:`, `refactor:`).
- Branches: `feature/<short-name>` or `fix/<short-name>`.
- PRs must include: summary, rationale, user impact, test evidence (logs/output), and screenshots for UI changes; link related issues.

## Security & Configuration Tips
- Do not commit secrets, IPs, or tokens; use HA config entries or environment variables.
- Avoid hardcoded device paths; make them configurable (see `README.md` examples).
- Replace placeholder links with `bobo/android-tv-box` to match manifest.
