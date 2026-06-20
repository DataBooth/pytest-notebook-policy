## 🧪 Notebook policy report

| Metric | Value |
|---|---|
| Status | ⚠️ Findings |
| Generated | `2026-05-30 23:07:51 UTC` |
| Runtime | `0.00s` |
| Files scanned | `1` |
| Violations | `2` |

### 🔎 Findings

| File | Rule | Line | What | Why this is undesirable | Suggested fix |
|---|---|---:|---|---|---|
| `tests/fixtures/real/gallery_earthquake.py` | [`M001`](https://github.com/DataBooth/pytest-notebook-policy/blob/main/docs/RULES.md#m001) | `53` | Prefer reactive dependencies over on_change handlers. | Reactive dataflow is easier to reason about than callback-style imperative updates. | Prefer derived-cell dependencies over `on_change` callbacks for state propagation. |
| `tests/fixtures/real/gallery_earthquake.py` | [`M001`](https://github.com/DataBooth/pytest-notebook-policy/blob/main/docs/RULES.md#m001) | `66` | Prefer reactive dependencies over on_change handlers. | Reactive dataflow is easier to reason about than callback-style imperative updates. | Prefer derived-cell dependencies over `on_change` callbacks for state propagation. |

### 🧭 Notebook surface summary

| Category | Count |
|---|---:|
| Key imports | `2` |
| File references | `0` |
| HTTP requests | `1` |
| Data sources | `0` |

#### Key imports

| Import |
|---|
| `marimo` |
| `openlayers` |

#### File references

| File | Reference |
|---|---|
| `(none)` | `(none)` |

#### HTTP requests

| File | Endpoint |
|---|---|
| `tests/fixtures/real/gallery_earthquake.py` | `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson` |

#### Data sources

| File | Source |
|---|---|
| `(none)` | `(none)` |

## Appendix A — Configuration

| Setting | Value |
|---|---|
| Enabled rules/prefixes | `J001, J002, J011, J012, J013, M001, M002, M003, M004, M005, M006` |
| Ignored rules/prefixes | `(none)` |
| Jupyter source mode | `ipynb` |
| Jupyter max code cells | `20` |
| Jupyter max cell lines | `80` |
| Jupyter max inline definitions | `3` |
| Dependency enrichment | `False` |
| NBOM output path | `/Users/mjboothaus/code/github/databooth/pytest-notebook-policy/reports/fixtures-real/marimo/gallery_earthquake/notebook-policy-nbom.json` |

## Appendix B — Scanned files

| File | Type |
|---|---|
| `tests/fixtures/real/gallery_earthquake.py` | `.py` |
