# Just setup
This repository includes a `justfile` with common local workflows for validation and release preparation.

## What is Just?
Just is a command runner similar to `make`, with a simpler syntax.

Official site: https://just.systems

Installation instructions: https://just.systems/man/en/

## Quick start
From the repository root, list available recipes:

```shell
just --list
```

## Key recipes in this repository
- `just create-manual-examples`: scaffold manual marimo/Jupyter example notebooks in `manual_checks/`.
- `just refresh-fixtures`: print observed rule-code sets for pinned real fixtures.
- `just qa`: run Ruff and tests.
- `just docs-init`: initialise Great Docs configuration (`great-docs.yml`).
- `just docs-build`: build the docs site into `great-docs/_site`.
- `just docs-preview`: preview docs locally with live reload.
- `just docs-scan`: scan discovered exports for API docs coverage.
- `just docs-setup-pages`: scaffold GitHub Pages workflow via Great Docs.
- `just docs-check`: prepublish link check (ignores known not-yet-live URLs).
- `just docs-check-strict`: strict link check with no ignores.
- `just docs-workflow`: run the default docs build + prepublish checks.
- `just docs-workflow-strict`: run build + strict checks.
- `just build-check`: clean artefacts, build, and run `twine check`.
- `just test-publish-dry-run`: build and validate publish artefacts without uploading.

## Recommended sequence before manual notebook validation
1. `just create-manual-examples`
2. `uv run pytest-notebook-quality --skip-ruff manual_checks`
3. Follow `MANUAL_NOTEBOOK_VALIDATION.md` for remediation and sign-off.
