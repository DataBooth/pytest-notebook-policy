# Release notes
This project follows Semantic Versioning (`MAJOR.MINOR.PATCH`).

## [Unreleased]
### Changed
- No unreleased entries yet.

## [1.0.0] - Stable baseline + Great Docs foundation
### Release intent
- Mark the first stable major release and establish a modern runtime/docs baseline for ongoing development.

### Highlights
- Promoted package versioning to `1.0.0`.
- Raised runtime support baseline to Python `3.12+`.
- Updated Ruff target configuration to `py312`.
- Added Great Docs integration for documentation generation and preview workflows.
- Added GitHub Pages docs workflow scaffold via Great Docs (`.github/workflows/docs.yml`).
- Expanded CI test matrix to validate against Python `3.12` and `3.13`.

## [0.9.0] - Report UX and NBOM alignment
### Release intent
- Improve markdown report readability and operator guidance while keeping machine-readable NBOM output aligned.

### Highlights
- Refactored markdown report rendering to use a Jinja2 template.
- Added standard executive summary guidance under the report header.
- Added short descriptive text under major report sections to clarify purpose and usage.
- Added Appendix C NBOM alignment summary fields for easier cross-checking against NBOM JSON output.
- Shifted optional dependency metadata to Appendix D when enrichment is enabled.
- Added regression assertions for updated report structure and section ordering.

## [0.8.0] - Planned initial PyPI release
### Release intent
- First public release of `pytest-notebook-policy` to PyPI.
- Align package name, CLI commands, and repository documentation under the same project identity.

### Highlights
- marimo notebook policy rules (`M001` to `M006`) for:
  - callback usage (`on_change`)
  - mixed test/helper cell structure
  - mutable module-level state
  - fixture placement in notebooks
  - cross-cell mutation of shared objects
  - non-idempotent runtime calls
- Jupyter notebook policy rules (`J001`, `J002`, `J010`, `J011`, `J012`, `J013`) for:
  - magics/shell escapes
  - non-idempotent calls
  - paired `.ipynb`/`.py` sync checks (opt-in)
  - parameter/configuration cell presence
  - notebook/cell size limits
  - inline definition complexity limits
- Combined quality command: `pytest-notebook-quality`.
- Deterministic rule selection and threshold tuning via CLI and `pyproject.toml`.
- Markdown report generation with rule guidance and remediation suggestions.
- Expanded fixture coverage (synthetic + real-world notebooks) and fixture refresh automation.
- CI/pre-commit automation for lint and test quality gates.

### Packaging and publish checklist
- Confirm version in `pyproject.toml` matches this release (`0.8.0`).
- Build distributions:
  - `uv build`
- Validate distributions:
  - `uv run --with twine twine check dist/*`
- Verify locally in a clean environment:
  - install wheel/sdist
  - run `pytest-notebook-quality --help`
  - run a sample notebook quality check
- Publish to PyPI:
  - `uv run --with twine twine upload dist/*`
