# Contributing to lrc-tools

Thanks for your interest! This project aims to be small, stable, and useful. We keep scope tight on purpose.

## Before contributing

1. Check existing issues / PRs to avoid duplication.
2. Open an issue first for feature requests — not all ideas fit the project scope.
3. For bugs, include the command you ran, your OS, Python version, and full error output.

## Development setup

```bash
git clone https://github.com/RicknotDev/lrc-tools
cd lrc-tools
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install -e ".[full]"
```

## Guidelines

- **Keep it simple.** No new dependencies unless the stdlib truly can't do it.
- **Tests must pass.** Run `python -m unittest discover -s tests` before pushing.
- **One change per PR.** Small, focused PRs get reviewed faster.
- **No boilerplate.** If a function can be 3 lines, don't make it 10.

## Code style

- Target Python 3.12+
- Run `ruff check src/ tests/` before submitting
- Use type hints
- No comments unless the intent isn't obvious from the code

## Project layout

```
src/lrc_tools/       # source
tests/               # tests (stdlib unittest)
scripts/             # dev/build scripts
```

## Release process

Tags `v*.*.*` trigger automated PyPI publish + binary builds via CI.
