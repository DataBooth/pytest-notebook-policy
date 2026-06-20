default:
  @just --list

bump-1_0_0:
  uv version 1.0.0

clean-release-artifacts:
  uv run python scripts/clean_release_artifacts.py
create-manual-examples:
  uv run python scripts/create_manual_examples.py

refresh-fixtures:
  uv run python scripts/refresh_real_fixtures.py --report-only
notebook-policy-report paths report='reports/notebook-policy-report.md':
  uv run pytest-notebook-quality --skip-ruff \
    --notebook-check-select M \
    --notebook-check-select J \
    --notebook-check-ignore J010 \
    --report-md {{report}} \
    {{paths}}

qa:
  uv run ruff check src tests scripts
  uv run python -m pytest tests

docs-build:
  uv run great-docs build

docs-preview:
  uv run great-docs preview
docs-init:
  uv run great-docs init

docs-setup-pages:
  uv run great-docs setup-github-pages

docs-scan:
  uv run great-docs scan

docs-check: docs-build
  uv run great-docs check-links \
    --ignore "https://databooth.github.io/pytest-notebook-policy/?$" \
    --ignore "https://github.com/DataBooth/pytest-notebook-policy/actions/workflows/ci\\.yml/badge\\.svg" \
    --ignore "https://github.com/DataBooth/pytest-notebook-policy/blob/main/pytest_notebook_policy/.*"

docs-check-strict: docs-build
  uv run great-docs check-links

docs-workflow: docs-build docs-check

docs-workflow-strict: docs-build docs-check-strict

build-check: clean-release-artifacts
  uv build
  uv run --with twine twine check dist/*
test-publish-dry-run: build-check
  uv run python -c "from pathlib import Path; dist=Path('dist'); files=sorted(list(dist.glob('*.whl')) + list(dist.glob('*.tar.gz'))); assert files, 'No build artefacts found in dist/'; assert all(file.name.startswith('pytest_notebook_policy-') for file in files), 'Unexpected non-target artefact found in dist/'; print('\n'.join(str(file) for file in files))"

prepare-1_0_0: refresh-fixtures qa build-check
