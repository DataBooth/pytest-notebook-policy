# Contributing
Thanks for contributing to `pytest-notebook-policy`.

## Prerequisites
- Python `3.12+`
- `uv` for environment and dependency management
- `just` (optional but recommended for common workflows)

## Quick local workflow
1. Sync dependencies:
   - `uv sync --dev`
2. Run quality gates:
   - `just qa`
3. Build docs:
   - `just docs-build`

## Documentation workflow (Great Docs)
Use this as the default docs gate before opening a PR:

- `just docs-workflow`

This runs:
- docs build (`great-docs build`)
- prepublish link checks with sensible temporary ignores for not-yet-live URLs

For strict enforcement (for example after Pages is live and branch/source links are stable), run:

- `just docs-workflow-strict`

Useful docs commands:
- `just docs-preview` (local preview with reload)
- `just docs-scan` (API discovery view)
- `just docs-setup-pages` (scaffold/refresh GitHub Pages workflow)

## Release-related checks
Before packaging/release work:
- `just qa`
- `just build-check`

## Pull requests
- Keep changes scoped and explain intent in the PR description.
- Include validation commands/results for code and docs where relevant.
- Update docs and release notes when behaviour or user-facing workflows change.
