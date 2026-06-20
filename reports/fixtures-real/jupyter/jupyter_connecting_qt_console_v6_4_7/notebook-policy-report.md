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
| `tests/fixtures/real/jupyter_connecting_qt_console_v6_4_7.ipynb` | [`J001`](https://github.com/DataBooth/pytest-notebook-policy/blob/main/docs/RULES.md#j001) | `1` | Avoid notebook magics/shell escapes in policy-checked notebooks; prefer Python code for reliable .ipynb↔.py sync. | Magics and shell escapes often reduce portability and reproducibility. | Replace magics/shell escapes with explicit Python equivalents where possible. |
| `tests/fixtures/real/jupyter_connecting_qt_console_v6_4_7.ipynb` | [`J001`](https://github.com/DataBooth/pytest-notebook-policy/blob/main/docs/RULES.md#j001) | `5` | Avoid notebook magics/shell escapes in policy-checked notebooks; prefer Python code for reliable .ipynb↔.py sync. | Magics and shell escapes often reduce portability and reproducibility. | Replace magics/shell escapes with explicit Python equivalents where possible. |

### 🧭 Notebook surface summary

| Category | Count |
|---|---:|
| Key imports | `0` |
| File references | `0` |
| HTTP requests | `0` |
| Data sources | `0` |

#### Key imports

| Import |
|---|
| `(none)` |

#### File references

| File | Reference |
|---|---|
| `(none)` | `(none)` |

#### HTTP requests

| File | Endpoint |
|---|---|
| `(none)` | `(none)` |

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
| NBOM output path | `/Users/mjboothaus/code/github/databooth/pytest-notebook-policy/reports/fixtures-real/jupyter/jupyter_connecting_qt_console_v6_4_7/notebook-policy-nbom.json` |

## Appendix B — Scanned files

| File | Type |
|---|---|
| `tests/fixtures/real/jupyter_connecting_qt_console_v6_4_7.ipynb` | `.ipynb` |
