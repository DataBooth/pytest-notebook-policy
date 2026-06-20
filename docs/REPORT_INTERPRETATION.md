# Report interpretation and policy tuning
Use this guide to interpret `pytest-notebook-policy` outputs and tune rules without losing delivery speed.

## 1) Interpreting the markdown report
When you run:

```shell
uv run pytest-notebook-quality --skip-ruff --report-md reports/notebook-policy-report.md notebooks/
```

the markdown report gives you:

- status summary (`Pass` or `Findings`)
- findings table with rule code, line, rationale, and suggested fix
- notebook surface summary (imports, files, HTTP endpoints, data sources)
- configuration appendix (selected/ignored rules and thresholds)
- scanned-files appendix
- optional dependency appendix (when dependency enrichment is enabled)

Interpretation order that works well in practice. Use this sequence:

1. Read status and total violation count.
2. Group findings by rule code to find repeating patterns.
3. Prioritise high-impact reproducibility issues first (`M006`, `J002`, `J011`).
4. Address maintainability/shape issues next (`J012`, `J013`, `M005`).
5. Re-run and compare deltas, not just the latest absolute count.

## 2) Interpreting the NBOM report
When you run:

```shell
uv run pytest-notebook-quality --skip-ruff --report-nbom-json reports/notebook-policy-nbom.json notebooks/
```

the NBOM output is best used for:

- machine-readable policy evidence in CI
- notebook-to-dependency traceability
- change tracking over time (violations, imports, external touchpoints)

Use it to answer:

- what changed in notebook surface area between runs?
- which dependencies are newly introduced?
- which notebooks produce repeated policy violations?

## 3) Practical tuning workflow (proportionate and optional)
Use this loop when rules need to adapt as notebooks move from PoC to MVP to production.

1. Start with a proportionate baseline profile.
2. Run checks and capture reports.
3. Fix repeated high-value findings first.
4. Tune only when false positives or deliberate exceptions are clear.
5. Record tuned defaults in `pyproject.toml`.
6. Reassess profile strictness at each lifecycle transition (PoC → MVP → production).

## 4) What to tune first
Prefer tuning in this order:

1. `ignore` list for explicit, justified exceptions.
2. Jupyter thresholds (`jupyter_max_code_cells`, `jupyter_max_cell_lines`, `jupyter_max_inline_definitions`) for team context.
3. `select` scope once the team is ready for broader coverage.

Example defaults:

```toml
[tool.pytest_notebook_policy.quality]
select = ["M", "J"]
ignore = ["J010"]
jupyter_source = "paired-py"
jupyter_max_code_cells = 30
jupyter_max_cell_lines = 120
jupyter_max_inline_definitions = 5
report_md = "reports/notebook-policy-report.md"
report_nbom_json = "reports/notebook-policy-nbom.json"
```

## 5) Tuning anti-patterns to avoid
- Disabling broad rule families too early (`ignore = ["M", "J"]`).
- Using `ignore` instead of fixing repeated reproducibility issues.
- Tightening thresholds before the team has stabilised notebook structure.
- Treating PoC and production notebooks as the same risk class.

## 6) Recommended review cadence
- PoC: tune weekly while notebook shape is changing quickly.
- MVP: tune per release cycle.
- Production: tune only via explicit change review, with rationale captured in PR notes.
