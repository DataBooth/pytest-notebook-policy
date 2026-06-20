## 🧪 Notebook policy report

| Metric | Value |
|---|---|
| Status | ⚠️ Findings |
| Generated | `2026-05-30 23:07:51 UTC` |
| Runtime | `0.00s` |
| Files scanned | `1` |
| Violations | `3` |

### 🔎 Findings

| File | Rule | Line | What | Why this is undesirable | Suggested fix |
|---|---|---:|---|---|---|
| `tests/fixtures/real/jupyter_importing_notebooks_v6_4_7.ipynb` | [`J011`](https://github.com/DataBooth/pytest-notebook-policy/blob/main/docs/RULES.md#j011) | `1` | Add a top-of-notebook parameter/configuration cell (within the first three code cells) to make runs reproducible and easier to automate. | A clear parameter cell improves reproducibility and automation. | Add a top-of-notebook configuration/parameter code cell within the first three code cells. |
| `tests/fixtures/real/jupyter_importing_notebooks_v6_4_7.ipynb` | [`J013`](https://github.com/DataBooth/pytest-notebook-policy/blob/main/docs/RULES.md#j013) | `7` | Notebook defines 4 functions/classes inline; keep at most 3 and extract reusable logic into importable modules. | Too many inline definitions blur notebook narrative and reusable logic boundaries. | Extract reusable functions/classes into modules and keep notebooks focused on orchestration. |
| `tests/fixtures/real/jupyter_importing_notebooks_v6_4_7.ipynb` | [`J001`](https://github.com/DataBooth/pytest-notebook-policy/blob/main/docs/RULES.md#j001) | `108` | Avoid notebook magics/shell escapes in policy-checked notebooks; prefer Python code for reliable .ipynb↔.py sync. | Magics and shell escapes often reduce portability and reproducibility. | Replace magics/shell escapes with explicit Python equivalents where possible. |

### 🧭 Notebook surface summary

| Category | Count |
|---|---:|
| Key imports | `9` |
| File references | `8` |
| HTTP requests | `0` |
| Data sources | `0` |

#### Key imports

| Import |
|---|
| `IPython` |
| `io` |
| `nbformat` |
| `nbpackage` |
| `os` |
| `pygments` |
| `shutil` |
| `sys` |
| `types` |

#### File references

| File | Reference |
|---|---|
| `tests/fixtures/real/jupyter_importing_notebooks_v6_4_7.ipynb` | `.ipynb` |
| `tests/fixtures/real/jupyter_importing_notebooks_v6_4_7.ipynb` | `<h4>%s cell</h4>` |
| `tests/fixtures/real/jupyter_importing_notebooks_v6_4_7.ipynb` | `<pre>%s</pre>` |
| `tests/fixtures/real/jupyter_importing_notebooks_v6_4_7.ipynb` | `<style type='text/css'> %s </style>` |
| `tests/fixtures/real/jupyter_importing_notebooks_v6_4_7.ipynb` | `find a notebook, given its fully qualified name and an optional path          This turns "foo.bar" into "foo/bar.ipynb"     and tries turning "Foo_Bar" into "Foo Bar" if Foo_Bar     does not exist.` |
| `tests/fixtures/real/jupyter_importing_notebooks_v6_4_7.ipynb` | `inside_ipython.ipynb` |
| `tests/fixtures/real/jupyter_importing_notebooks_v6_4_7.ipynb` | `mynotebook.ipynb` |
| `tests/fixtures/real/jupyter_importing_notebooks_v6_4_7.ipynb` | `other.ipynb` |

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
| NBOM output path | `/Users/mjboothaus/code/github/databooth/pytest-notebook-policy/reports/fixtures-real/jupyter/jupyter_importing_notebooks_v6_4_7/notebook-policy-nbom.json` |

## Appendix B — Scanned files

| File | Type |
|---|---|
| `tests/fixtures/real/jupyter_importing_notebooks_v6_4_7.ipynb` | `.ipynb` |
