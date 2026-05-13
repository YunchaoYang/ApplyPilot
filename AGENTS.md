# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

ApplyPilot is a Python CLI tool for autonomous job applications. It is a pure-Python package (no Docker, no external databases) using a file-based SQLite DB at `~/.applypilot/applypilot.db`. See `README.md` for full product description and `CONTRIBUTING.md` for dev setup.

### Development setup

After the update script runs, the environment is ready. Key commands from `CONTRIBUTING.md`:

- **Lint:** `ruff check src/` (pre-existing warnings exist in the codebase; exit code 1 is expected)
- **Format:** `ruff format src/`
- **Test:** `pytest tests/ -v` (the `tests/` directory may be empty — exit code 5 means no tests collected)
- **CLI:** `applypilot --version`, `applypilot doctor`, `applypilot status`, `applypilot --help`

### Non-obvious gotchas

- `$HOME/.local/bin` must be on `PATH` for the `applypilot` CLI entry point to work. The update script adds it.
- `python-jobspy` must be installed with `--no-deps` due to a strict numpy pin in its metadata that conflicts with modern numpy. Its actual runtime dependencies are installed separately. This is documented in `README.md`.
- `ruff check src/` currently returns exit code 1 due to ~32 pre-existing lint warnings (mostly unused imports). This is expected and does not indicate a setup problem.
- The `tests/` directory may not exist in the repo. Create it if you need to add tests; `pytest tests/ -v` handles a missing directory gracefully after creation.
- Stages 1-5 of the pipeline require a `GEMINI_API_KEY` (or `OPENAI_API_KEY` or `LLM_URL`) set in `~/.applypilot/.env`. Stage 6 (auto-apply) additionally requires Claude Code CLI, Chrome, and Node.js.
- The 3-tier system means the app functions at different levels: Tier 1 (discovery only), Tier 2 (+ AI scoring/tailoring), Tier 3 (+ auto-apply). Use `applypilot doctor` to check current tier.
