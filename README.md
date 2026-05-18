# pytest-marimo
`pytest-marimo` is a `pytest` plugin that enforces marimo notebook quality rules.

It is aimed at checks that are specific to marimo’s reactive notebook model, not generic Python linting.

## What this package is
`pytest-marimo` is a lightweight semantic checker for marimo notebooks that runs in Python tooling workflows.

It focuses on enforcing notebook patterns that are easy to miss in review, such as:
- `on_change` callback usage where reactivity is clearer
- cross-cell mutation of shared objects
- non-idempotent cell behaviour
- mixed test/helper cells and fixture placement conventions

## Why this package exists
marimo already gives you:
- native notebook testing with `pytest`
- built-in notebook linting via `marimo check` ([announcement](https://marimo.io/blog/marimo-check))

`pytest-marimo` is designed to complement those tools with opinionated, team-level checks tailored to a stricter “production notebook” style.

In practice:
- use **Ruff** for general Python quality/security
- use **marimo check** for core notebook validity and formatting rules
- use **pytest-marimo** for extra policy checks around reactive design and notebook maintainability

## Machine-assisted coding guardrails
`pytest-marimo` is especially useful as an automated quality gate when notebooks are generated or edited by coding agents (for example Claude, Warp, Codex, or similar tools).

Adding it to pre-commit and CI helps catch marimo-specific issues immediately, so agents can self-correct before code reaches review.

Example pre-commit hook:

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest-marimo-quality
        name: pytest-marimo-quality
        entry: uv run pytest-marimo-quality experiments notebooks
        language: system
        pass_filenames: false
```

This keeps the feedback loop short:
- agent proposes notebook edits
- pre-commit/CI runs Ruff + `pytest-marimo` checks
- agent fixes violations and retries

## Current rules
- `M001`: prefer reactive dependencies over `on_change` handlers.
- `M002`: keep test cells focused; avoid mixing tests with helper/setup code in the same cell.
- `M003`: avoid mutable module-level state in notebook files.
- `M004`: prefer fixtures in `conftest.py` or helper modules rather than notebook modules.
- `M005`: avoid cross-cell mutation of shared objects (including notebook inputs and module-level mutable state).
- `M006`: avoid non-idempotent calls in cells (for example `random.*`, `np.random.*`, `time.time`, `uuid.uuid4`).

## Usage
Install in a project:

```shell path=null start=null
uv add --dev pytest-marimo
```

Run checks explicitly:

```shell path=null start=null
uv run pytest --marimo-check
```

Enable by default in `pyproject.toml`:

```toml path=null start=null
[tool.pytest.ini_options]
marimo_check = true
```

Filter rules:

```shell path=null start=null
uv run pytest --marimo-check --marimo-check-select M001 --marimo-check-ignore M004
```

Run combined Ruff + pytest-marimo semantic checks:

```shell path=null start=null
uv run pytest-marimo-quality path/to/notebooks
```

Skip Ruff and run only pytest-marimo semantic checks:

```shell path=null start=null
uv run pytest-marimo-quality --skip-ruff path/to/notebooks
```
## Notebook fixtures for testing
The repository includes notebook fixtures in `tests/fixtures`:

- `tests/fixtures/synthetic`: synthetic notebooks for targeted pass/fail checks.
- `tests/fixtures/real`: real-world notebooks sourced from public marimo repositories (with provenance in `tests/fixtures/real/SOURCES.txt`).
