# Getting Started

This page explains how to set up a development environment and run the GUI locally.

## Prerequisites

- Python 3.10 or newer

## Create a virtual environment

Use a venv in the project root so dependencies don't leak into the system Python.

```bash
python -m venv .venv
source .venv/Scripts/activate
# If you use PowerShell run instead:
. .venv\Scripts\Activate.ps1
```

## Install dependencies

The project contains pinned developer dependencies in `dev-requirements.txt`. Installing these gives you the tools for running the app, tests and building the docs.

```bash
pip install --upgrade pip
pip install -r dev-requirements.txt
```

If you prefer a minimal runtime install (faster) you can install only the runtime deps with:

```bash
pip install -r requirements.txt
```

Notes:

- The project uses `pyproject.toml` for dependency metadata. The developers used `pip-tools` to produce pinned `dev-requirements.txt` and `requirements.txt`.
- If you need to add or update dependencies follow the pattern in the README using `pip-compile`.

## Run the GUI

Start the application with the module runner:

```bash
python -m solidity_gui
```

## Running tests

To run the test suite (pytest) after installing dev dependencies:

```bash
pytest -q
```

## Build a standalone executable

The project includes a PyInstaller spec in `Solidity-GUI.spec`. After installing the developer dependencies, you can build the executable with:

```bash
pyinstaller Solidity-GUI.spec
```

The built executable will appear in `dist/`.

## Editing and Publishing Documentation

Documentation is written in Markdown files in the [`docs`](docs) directory. To edit or add documentation, simply update or create `.md` files there.

To preview the MkDocs site locally:

```bash
mkdocs serve
# Open http://127.0.0.1:8000 in a browser
```

To publish updates, commit your changes and push to the main branch. Documentation is automatically deployed to GitHub Pages via the CI workflow ([`.github/workflows/docs.yml`](.github/workflows/docs.yml)).

For more details on MkDocs, see [mkdocs.org](https://www.mkdocs.org/).

## Where to go next

- `docs/user_guide.md` — GUI walkthrough and common user tasks
- `docs/developer.md` — developer notes (existing)
- `README.md` — project overview and bundling notes
