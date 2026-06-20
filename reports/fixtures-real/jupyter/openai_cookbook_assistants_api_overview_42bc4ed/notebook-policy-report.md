## 🧪 Notebook policy report

| Metric | Value |
|---|---|
| Status | ⚠️ Findings |
| Generated | `2026-05-30 23:07:52 UTC` |
| Runtime | `0.00s` |
| Files scanned | `1` |
| Violations | `5` |

### 🔎 Findings

| File | Rule | Line | What | Why this is undesirable | Suggested fix |
|---|---|---:|---|---|---|
| `tests/fixtures/real/openai_cookbook_assistants_api_overview_42bc4ed.ipynb` | [`J001`](https://github.com/DataBooth/pytest-notebook-policy/blob/main/docs/RULES.md#j001) | `1` | Avoid notebook magics/shell escapes in policy-checked notebooks; prefer Python code for reliable .ipynb↔.py sync. | Magics and shell escapes often reduce portability and reproducibility. | Replace magics/shell escapes with explicit Python equivalents where possible. |
| `tests/fixtures/real/openai_cookbook_assistants_api_overview_42bc4ed.ipynb` | [`J011`](https://github.com/DataBooth/pytest-notebook-policy/blob/main/docs/RULES.md#j011) | `1` | Add a top-of-notebook parameter/configuration cell (within the first three code cells) to make runs reproducible and easier to automate. | A clear parameter cell improves reproducibility and automation. | Add a top-of-notebook configuration/parameter code cell within the first three code cells. |
| `tests/fixtures/real/openai_cookbook_assistants_api_overview_42bc4ed.ipynb` | [`J012`](https://github.com/DataBooth/pytest-notebook-policy/blob/main/docs/RULES.md#j012) | `1` | Notebook has 31 code cells; keep notebooks under 20 code cells or split into smaller notebooks/modules. | Large notebooks or very long cells are harder to review and maintain. | Split notebooks/cells into smaller units and move complex logic into importable modules. |
| `tests/fixtures/real/openai_cookbook_assistants_api_overview_42bc4ed.ipynb` | [`J001`](https://github.com/DataBooth/pytest-notebook-policy/blob/main/docs/RULES.md#j001) | `3` | Avoid notebook magics/shell escapes in policy-checked notebooks; prefer Python code for reliable .ipynb↔.py sync. | Magics and shell escapes often reduce portability and reproducibility. | Replace magics/shell escapes with explicit Python equivalents where possible. |
| `tests/fixtures/real/openai_cookbook_assistants_api_overview_42bc4ed.ipynb` | [`J013`](https://github.com/DataBooth/pytest-notebook-policy/blob/main/docs/RULES.md#j013) | `7` | Notebook defines 10 functions/classes inline; keep at most 3 and extract reusable logic into importable modules. | Too many inline definitions blur notebook narrative and reusable logic boundaries. | Extract reusable functions/classes into modules and keep notebooks focused on orchestration. |

### 🧭 Notebook surface summary

| Category | Count |
|---|---:|
| Key imports | `4` |
| File references | `1` |
| HTTP requests | `0` |
| Data sources | `0` |

#### Key imports

| Import |
|---|
| `json` |
| `openai` |
| `os` |
| `time` |

#### File references

| File | Reference |
|---|---|
| `tests/fixtures/real/openai_cookbook_assistants_api_overview_42bc4ed.ipynb` | `data/language_models_are_unsupervised_multitask_learners.pdf` |

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
| NBOM output path | `/Users/mjboothaus/code/github/databooth/pytest-notebook-policy/reports/fixtures-real/jupyter/openai_cookbook_assistants_api_overview_42bc4ed/notebook-policy-nbom.json` |

## Appendix B — Scanned files

| File | Type |
|---|---|
| `tests/fixtures/real/openai_cookbook_assistants_api_overview_42bc4ed.ipynb` | `.ipynb` |
