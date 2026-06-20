# Manual notebook validation and authoring guide
Use this guide when you want to manually confirm policy behaviour on real notebooks, including:

- creating new notebooks that should pass policy checks
- importing complex notebooks and remediating them to compliance
- validating both marimo (`.py`) and Jupyter (`.ipynb`) workflows

This guide also serves as a practical notebook **best-practice assurance** and **testing** checklist for teams who want explicit manual validation before release.

## Scope
This guide is intentionally practical. It assumes you want to test behaviour locally before publishing.

## 1) One-time setup for manual checks
Create a scratch area:

```shell
mkdir -p manual_checks/marimo manual_checks/jupyter
```

Or use the built-in recipe to scaffold known examples:

```shell
just create-manual-examples
```

For Just installation and recipe usage, see [`JUST_SETUP.md`](JUST_SETUP.md).

Run policy checks directly:

```shell
uv run pytest-notebook-quality --skip-ruff manual_checks
```

Optional pre-commit hook (local/manual usage):

```yaml
repos:
  - repo: local
    hooks:
      - id: notebook-policy-manual
        name: notebook-policy-manual
        entry: uv run pytest-notebook-quality --skip-ruff manual_checks
        language: system
        pass_filenames: false
```

Then run:

```shell
uv run --with pre-commit pre-commit run notebook-policy-manual --all-files
```

## 2) New notebook guide (`.ipynb` and `.py`)
Use these defaults to avoid common violations from the start.
### 2.0 Initialisation: clean isolated environment for notebook experiments
Create an isolated workspace and environment before authoring new notebooks:

```shell
mkdir -p manual_checks/experiments
cd manual_checks/experiments
uv init --python 3.13
uv add --dev pytest-notebook-policy
uv add --dev 'pytest-notebook-policy[sync]'
```

Notes:

- `uv init` creates a clean local project scaffold for experiments.
- `uv add --dev pytest-notebook-policy` installs the policy checker for manual validation.
- `'pytest-notebook-policy[sync]'` enables paired `.ipynb` ↔ `.py` sync support (useful when testing `J010`/paired-source workflows).

Quick verification:

```shell
uv run pytest --version
uv run pytest-notebook-quality --help
```

### 2.1 New Jupyter notebook (`.ipynb`) that is policy-friendly
Recommended structure:

1. First code cell: parameter/configuration cell (`J011`)
2. Keep code cells compact and focused (`J012`)
3. Avoid magics/shell escapes (`J001`)
4. Keep non-idempotent operations explicit and controlled (`J002`)
5. Move reusable classes/functions into modules (`J013`)

Suggested first code cell (parameters):

```python
params = {
    "seed": 42,
    "dataset_path": "data/train.csv",
    "run_mode": "dev",
}
```

Suggested workflow:

- Keep each cell focused on one transformation step.
- Move reusable logic to `src/...` modules and import it.
- If you use randomness/time/UUIDs, gate it behind explicit parameters.

Validate:

```shell
uv run pytest-notebook-quality --skip-ruff path/to/notebook.ipynb
```

### 2.2 New marimo notebook (`.py`) that is policy-friendly
Recommended structure:

1. Avoid `on_change` handlers where pure reactivity is enough (`M001`)
2. Avoid mutable module-level state (`M003`)
3. Avoid cross-cell mutation patterns (`M005`)
4. Keep non-idempotent calls controlled (`M006`)
5. Keep fixtures out of notebook modules (`M004`)

Suggested authoring defaults:

- treat cells as pure transformations where possible
- return new values instead of mutating shared inputs
- keep state local to cells/functions

Validate:

```shell
uv run pytest-notebook-quality --skip-ruff path/to/notebook.py
```

## 3) Second-stage checklist for complex imported notebooks
Use this when a real-world notebook fails several J-rules at once.

### Stage A: Baseline
1. Copy the candidate notebook into `manual_checks/...`.
2. Run:

```shell
uv run pytest-notebook-quality --skip-ruff manual_checks/jupyter/<notebook>.ipynb
```

3. Record initial codes and count (for example: `J001`, `J011`, `J012`, `J013`).

### Stage B: Rule-by-rule remediation order (recommended)
Apply in this order to reduce rework.

1. `J011` first: add a top-of-notebook parameter/configuration cell.
2. `J001`: remove magics and shell escapes; replace with Python APIs.
3. `J013`: extract inline classes/functions into importable modules.
4. `J012`: split large notebooks and long cells after extraction work.
5. `J002`: make non-idempotent behaviour explicit/controlled.
6. `J010` (if using paired files): verify `.ipynb` and paired `.py` stay in sync.

### Stage C: Verification gates
After each remediation step:

```shell
uv run pytest-notebook-quality --skip-ruff manual_checks/jupyter/<notebook>.ipynb
```

When stable, run on the whole manual check area:

```shell
uv run pytest-notebook-quality --skip-ruff manual_checks
```

If using pre-commit:

```shell
uv run --with pre-commit pre-commit run notebook-policy-manual --all-files
```

### Stage D: Compliance sign-off
Consider the notebook compliant when:

- no rule violations are reported for the target files
- extracted reusable logic lives in modules (not large inline cells)
- parameter/configuration intent is clear in the first code cell
- the notebook remains readable and reviewable

## 4) Optional paired-source check for Jupyter notebooks
If you maintain paired `.ipynb`/`.py` notebooks, run with paired source mode:

```shell
uv run pytest --notebook-check --notebook-check-jupyter-source paired-py path/to/notebook.ipynb
```

Use this when you want J-rules to evaluate the paired `.py` representation while still enforcing sync rules.
