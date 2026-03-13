# pip/AGENTS.md

This directory contains the **Python Server** implementation for Exots.

## Tech Stack
- **Language:** Python 3.10+
- **Package Manager:** `uv` (with `pyproject.toml` + `uv.lock`)
- **Type Checking:** Type hints throughout; `py.typed` marker included

## Key Commands
- **Install/Sync (dev env):** `uv sync --dev`
- **Run Tooling:** `uv run <command>`
- **Build:** Copy root LICENSE/README then `uv run python -m build`
- **Pack:** `uv run python -m build` (produces sdist and wheel in `dist/`)

## Development Workflow
1.  Make changes to the Python code in `src/exots/`.
2.  Integration tests are in `gem/spec/` (Ruby side), run with `bundle exec rspec spec/lib/exots/client_python_spec.rb`.
3.  The package has zero runtime dependencies (stdlib only).
4.  Lock dependencies with `uv lock` after dependency changes and commit `uv.lock`.
5.  To build, copy `../LICENSE` and `../README.md` into this directory, then run `uv run python -m build`.

## Code Style
- **Formatting:** Follow PEP 8 conventions.
- **Type Hints:** All public functions and methods must have type annotations.
- **Naming:** `snake_case` for functions, methods, variables; `PascalCase` for classes.
- **No External Dependencies:** Only use the Python standard library at runtime.

Note: Do not manually edit `pip/LICENSE` or `pip/README.md`. These are copied from the project root during the build process.
