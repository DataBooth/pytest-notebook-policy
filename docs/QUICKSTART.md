# Quickstart
This quickstart shows the fastest path to run `pytest-notebook-policy` in a project.
Runtime baseline: Python `3.12+`.

## 1) Install
Add as a development dependency:

```shell
uv add --dev pytest-notebook-policy
```

## 2) Run checks on a notebook
Run semantic checks with pytest:

```shell
uv run pytest --notebook-check path/to/notebook.py
```

Run semantic checks across multiple notebooks:

```shell
uv run pytest --notebook-check notebooks/
```

## 3) Interpret findings
Current rule codes:

- `M001`: prefer reactive dependencies over `on_change` handlers.
- `M002`: avoid mixing tests and helpers in the same cell.
- `M003`: avoid mutable module-level state.
- `M004`: keep fixtures out of notebook modules.
- `M005`: avoid cross-cell mutation of shared objects.
- `M006`: avoid non-idempotent calls in cells.
- `J001`: avoid notebook magics and shell escapes.
- `J002`: avoid non-idempotent calls in Jupyter code cells.
- `J010`: optional sync rule for paired `.ipynb` and `.py` notebooks.
- `J011`: require a top-of-notebook parameter/configuration cell.
- `J012`: keep notebooks and cells short enough to stay maintainable.
- `J013`: avoid excessive inline definitions; move reusable logic to modules.

Detailed rationale and remediation guidance: [`RULES.md`](RULES.md).
Report interpretation and policy-tuning workflow: [`REPORT_INTERPRETATION.md`](REPORT_INTERPRETATION.md).

## 4) Optional: start with a proportionate rule profile
Choose a baseline that matches your notebook context, then tighten over time.

PoC / exploratory (fast iteration with core guardrails):

```shell
uv run pytest-notebook-quality --skip-ruff \
  --notebook-check-select M001 \
  --notebook-check-select M003 \
  --notebook-check-select M006 \
  --notebook-check-select J011 \
  notebooks/
```

MVP / delivery hardening (maintainability + reproducibility):

```shell
uv run pytest-notebook-quality --skip-ruff \
  --notebook-check-select M \
  --notebook-check-select J001 \
  --notebook-check-select J002 \
  --notebook-check-select J011 \
  --notebook-check-select J012 \
  --notebook-check-select J013 \
  --notebook-check-ignore J010 \
  notebooks/
```

Production / operational (full policy set):

```shell
uv run pytest-notebook-quality --skip-ruff \
  --notebook-check-select M \
  --notebook-check-select J \
  notebooks/
```

Equivalent project defaults:

```toml
[tool.pytest_notebook_policy.quality]
# PoC profile example:
# select = ["M001", "M003", "M006", "J011"]

# MVP profile example:
# select = ["M", "J001", "J002", "J011", "J012", "J013"]
# ignore = ["J010"]

# Production profile example:
select = ["M", "J"]
```

## 5) Optional: enable by default
Add to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
notebook_check = true
```

Prefer paired `.py` notebooks for Jupyter rule checks:

```toml
[tool.pytest.ini_options]
notebook_check = true
notebook_check_jupyter_source = "paired-py"
```

Or set it on the command line:

```shell
uv run pytest --notebook-check --notebook-check-jupyter-source paired-py notebooks/
```

Tune J012/J013 thresholds:

```shell
uv run pytest --notebook-check \
  --notebook-check-jupyter-max-code-cells 30 \
  --notebook-check-jupyter-max-cell-lines 120 \
  --notebook-check-jupyter-max-inline-definitions 5 notebooks/
```

Or set defaults:

```toml
[tool.pytest.ini_options]
notebook_check_jupyter_max_code_cells = "30"
notebook_check_jupyter_max_cell_lines = "120"
notebook_check_jupyter_max_inline_definitions = "5"
```

## 6) Optional: run combined quality checks
Run Ruff and notebook policy checks together:

```shell
uv run pytest-notebook-quality notebooks/
```

Skip Ruff and run only semantic checks:

```shell
uv run pytest-notebook-quality --skip-ruff notebooks/
```

Customise rule toggles and thresholds:

```shell
uv run pytest-notebook-quality --skip-ruff \
  --notebook-check-select M \
  --notebook-check-select J \
  --notebook-check-ignore J010 \
  --notebook-check-jupyter-source paired-py \
  --notebook-check-jupyter-max-code-cells 30 \
  --notebook-check-jupyter-max-cell-lines 120 \
  --notebook-check-jupyter-max-inline-definitions 5 \
  notebooks/
```

Write an NBOM-style JSON manifest:

```shell
uv run pytest-notebook-quality --skip-ruff \
  --report-nbom-json reports/notebook-policy-nbom.json \
  --report-dependency-enrichment \
  notebooks/
```
Include optional vulnerability IDs (queried from OSV):

```shell
uv run pytest-notebook-quality --skip-ruff \
  --report-nbom-json reports/notebook-policy-nbom.json \
  --report-dependency-vulns \
  notebooks/
```
`--report-dependency-vulns` implicitly enables dependency enrichment.

Write a markdown report (with why/remediation guidance per finding):

```shell
uv run pytest-notebook-quality --skip-ruff --report-md reports/notebook-policy-report.md notebooks/
```

Add optional dependency enrichment to include import-to-package metadata:

```shell
uv run pytest-notebook-quality --skip-ruff \
  --report-md reports/notebook-policy-report.md \
  --report-dependency-enrichment \
  notebooks/
```

Set project-specific defaults in `pyproject.toml`:

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

## 7) Optional: prek hook
Example local hook:

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest-notebook-quality
        name: pytest-notebook-quality
        entry: uv run pytest-notebook-quality notebooks
        language: system
        pass_filenames: false
```

Install and run hooks:

```shell
uv run prek install
uv run prek run pytest-notebook-quality --all-files
```

## 8) Manual validation and remediation workflow
For a full manual testing walkthrough (including complex notebook remediation and new notebook authoring guidance for both `.ipynb` and `.py`), see:

- [`MANUAL_NOTEBOOK_VALIDATION.md`](MANUAL_NOTEBOOK_VALIDATION.md)
