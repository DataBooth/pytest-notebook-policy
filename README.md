# pytest-notebook-policy
[![CI](https://github.com/DataBooth/pytest-notebook-policy/actions/workflows/ci.yml/badge.svg)](https://github.com/DataBooth/pytest-notebook-policy/actions/workflows/ci.yml)
`pytest-notebook-policy` is a `pytest` plugin that enforces notebook policy and quality rules.

It focuses on notebook-specific checks for marimo and Jupyter workflows, not generic Python linting.

## Terminology and discoverability
If you are looking for notebook **best practices**, **assurance**, **validation**, or **testing** tooling, this project is intended to cover those needs through enforceable policy checks and automated quality gates.

## What this package is
`pytest-notebook-policy` is a lightweight semantic checker for notebook workflows.

It focuses on enforcing notebook patterns that are easy to miss in review.

### Patterns checked
- `on_change` callback usage where reactivity is clearer
- cross-cell mutation of shared objects
- non-idempotent cell behaviour
- mixed test/helper cells and fixture placement conventions

## Why this package exists

### What marimo already covers
- native notebook testing with `pytest`
- built-in notebook linting via `marimo check` ([announcement](https://marimo.io/blog/marimo-check))

`pytest-notebook-policy` is designed to complement those tools with opinionated, team-level checks tailored to a stricter “production notebook” style.

### In practice
- use **Ruff** for general Python quality/security
- use **marimo check** for core notebook validity and formatting rules
- use **pytest-notebook-policy** for extra policy checks around reactive design and notebook maintainability

## Machine-assisted coding guardrails
`pytest-notebook-policy` is especially useful as an automated quality gate when notebooks are generated or edited by coding agents (for example Claude, Warp, Codex, or similar tools).

Adding it to prek hooks and CI helps catch marimo-specific issues immediately, so agents can self-correct before code reaches review.

Example prek hook configuration:

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest-notebook-quality
        name: pytest-notebook-quality
        entry: uv run pytest-notebook-quality experiments notebooks
        language: system
        pass_filenames: false
```

### Feedback loop
- agent proposes notebook edits
- prek/CI runs Ruff + `pytest-notebook-policy` checks
- agent fixes violations and retries

## Current rules
- `M001`: prefer reactive dependencies over `on_change` handlers.
- `M002`: keep test cells focused; avoid mixing tests with helper/setup code in the same cell.
- `M003`: avoid mutable module-level state in notebook files.
- `M004`: prefer fixtures in `conftest.py` or helper modules rather than notebook modules.
- `M005`: avoid cross-cell mutation of shared objects (including notebook inputs and module-level mutable state).
- `M006`: avoid non-idempotent calls in cells (for example `random.*`, `np.random.*`, `time.time`, `uuid.uuid4`).
- `J001`: avoid notebook magics and shell escapes in policy-checked notebooks.
- `J002`: avoid non-idempotent calls in Jupyter notebook code cells.
- `J010`: (opt-in) check that paired `.ipynb` and `.py` files stay in sync.
- `J011`: require a top-of-notebook parameter/configuration cell in the first few code cells.
- `J012`: keep notebooks and cells small enough to stay reviewable and maintainable.
- `J013`: avoid excessive inline function/class definitions in notebooks; extract reusable logic into modules.
Detailed rationale and remediation guidance: [`docs/RULES.md`](docs/RULES.md).

## Usage
Runtime baseline: Python `3.12+`.
Install in a project:

```shell
uv add --dev pytest-notebook-policy
```

Install prek hooks:

```shell
uv run prek install
```

Run hooks across all files:

```shell
uv run prek run --all-files
```

CI runs on push/PR using `.github/workflows/ci.yml` and executes Ruff plus the test suite.

Run checks explicitly:

```shell
uv run pytest --notebook-check
```

Enable by default in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
notebook_check = true
```

Filter rules:

```shell
uv run pytest --notebook-check --notebook-check-select M001 --notebook-check-ignore M004
```

Choose Jupyter rule source:

```shell
uv run pytest --notebook-check --notebook-check-jupyter-source paired-py
```

Set default Jupyter rule source in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
notebook_check = true
notebook_check_jupyter_source = "paired-py"
```

`paired-py` prefers the paired `.py` notebook (when available and readable) for J-rules and falls back to `.ipynb`.

Tune Jupyter size/complexity thresholds:

```shell
uv run pytest --notebook-check \
  --notebook-check-jupyter-max-code-cells 30 \
  --notebook-check-jupyter-max-cell-lines 120 \
  --notebook-check-jupyter-max-inline-definitions 5
```

Set defaults in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
notebook_check_jupyter_max_code_cells = "30"
notebook_check_jupyter_max_cell_lines = "120"
notebook_check_jupyter_max_inline_definitions = "5"
```

Run combined Ruff + notebook policy checks:

```shell
uv run pytest-notebook-quality path/to/notebooks
```

Skip Ruff and run only notebook policy checks:

```shell
uv run pytest-notebook-quality --skip-ruff path/to/notebooks
```

Customise deterministic rule toggles and thresholds on the quality command:

```shell
uv run pytest-notebook-quality --skip-ruff \
  --notebook-check-select M \
  --notebook-check-select J \
  --notebook-check-ignore J010 \
  --notebook-check-jupyter-source paired-py \
  --notebook-check-jupyter-max-code-cells 30 \
  --notebook-check-jupyter-max-cell-lines 120 \
  --notebook-check-jupyter-max-inline-definitions 5 \
  path/to/notebooks
```

Write an NBOM-style JSON manifest (notebook surface + dependency correlation):

```shell
uv run pytest-notebook-quality --skip-ruff \
  --report-nbom-json reports/notebook-policy-nbom.json \
  --report-dependency-enrichment \
  path/to/notebooks
```
Include optional vulnerability IDs (queried from OSV) in dependency enrichment output:

```shell
uv run pytest-notebook-quality --skip-ruff \
  --report-nbom-json reports/notebook-policy-nbom.json \
  --report-dependency-vulns \
  path/to/notebooks
```
`--report-dependency-vulns` implicitly enables dependency enrichment.

Generate a markdown report with findings-first layout, touchpoint summary, and appendices:

```shell
uv run pytest-notebook-quality --skip-ruff --report-md reports/notebook-policy-report.md path/to/notebooks
```

Enable optional dependency enrichment in the report:

```shell
uv run pytest-notebook-quality --skip-ruff \
  --report-md reports/notebook-policy-report.md \
  --report-dependency-enrichment \
  path/to/notebooks
```
Interpret report outputs and tune policy profiles: [`docs/REPORT_INTERPRETATION.md`](docs/REPORT_INTERPRETATION.md).

Project-specific quality defaults can be set in `pyproject.toml`:

```toml
[tool.pytest_notebook_policy.quality]
select = ["M", "J"]
ignore = ["J010"]
jupyter_source = "paired-py"
jupyter_max_code_cells = 30
jupyter_max_cell_lines = 120
jupyter_max_inline_definitions = 5
report_md = "reports/notebook-policy-report.md"
report_dependency_enrichment = true
report_dependency_vulns = false
report_nbom_json = "reports/notebook-policy-nbom.json"
```

Enable optional sync tooling:

```shell
uv add --dev 'pytest-notebook-policy[sync]'
```

## Documentation site (Great Docs)
This repository uses Great Docs for documentation generation and deployment.

Build docs locally:

```shell
uv run great-docs build
```

Preview docs locally:

```shell
uv run great-docs preview
```

Scaffold or refresh the GitHub Pages workflow:

```shell
uv run great-docs setup-github-pages
```

## Versioning and release workflow
- Versioning follows Semantic Versioning (`MAJOR.MINOR.PATCH`).
- Release history lives in `RELEASE_NOTES.md`.

Typical release flow:

```shell
uv version --bump patch
uv build
uv run --with twine twine check dist/*
```

When ready to release (not run yet here), upload with Twine:

```shell
uv run --with twine twine upload dist/*
```
## Notebook fixtures for testing
The repository includes notebook fixtures in `tests/fixtures`:

- `tests/fixtures/synthetic`: synthetic notebooks for targeted pass/fail checks.
- `tests/fixtures/real`: real-world notebooks sourced from public repositories (with provenance in `tests/fixtures/real/SOURCES.txt`).

Refresh pinned real fixtures and print their observed rule-code sets:

```shell
uv run python scripts/refresh_real_fixtures.py
```
