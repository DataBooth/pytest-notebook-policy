# Rule reference
This page documents each implemented `pytest-notebook-policy` rule with intent, scope, and practical remediation guidance.

## Rule families and applicability
`pytest-notebook-policy` has two rule families:

- `M` rules: module-level behavioural rules for Python notebook modules (`.py`), including marimo notebooks and paired Jupyter Python sources.
- `J` rules: Jupyter-structure rules for Jupyter notebooks (`.ipynb`) and, where configured, their paired Python sources.

Practical interpretation:

- For marimo-first projects, `M` rules are usually the core baseline.
- For Jupyter-first projects, use both `M` and `J` rules.
- `J010` only matters when your team intentionally uses paired `.ipynb` + `.py` workflows.

## Proportionate adoption profiles (all optional)
All rules are optional. Teams can adopt them in stages based on context and risk.

### Profile 1: PoC / exploratory
Focus on rapid iteration with basic guardrails.

- Suggested selection: `M001`, `M003`, `M006`, `J011`
- Typical posture: guidance-heavy, low blocking, faster feedback loops

### Profile 2: MVP / delivery hardening
Add maintainability and reproducibility checks as usage broadens.

- Suggested selection: `M001-M006`, `J001`, `J002`, `J011`, `J012`, `J013`
- Optional: enable `J010` if your team relies on paired sources

### Profile 3: Production / operational
Treat notebooks as operational software assets with stronger controls.

- Suggested selection: all implemented `M` and `J` rules
- Typical posture: tighter thresholds for size/complexity rules and explicit policy exceptions when needed

This staged model reflects real notebook lifecycles where work can move quickly from PoC to MVP to production.

<a id="m001"></a>
## `M001` Prefer reactive dependencies over `on_change`
Applies to: marimo and Python notebook modules.
Why: callback-based state propagation can become hard to reason about in reactive notebooks.
How to fix: model dependencies explicitly so downstream cells derive values from inputs/state instead of callback side effects.

<a id="m002"></a>
## `M002` Keep test cells focused
Applies to: marimo and Python notebook modules.
Why: mixing assertions with setup/helper logic makes failures less clear.
How to fix: keep assertion logic in dedicated test cells and move setup/helpers into separate cells or modules.

<a id="m003"></a>
## `M003` Avoid mutable module-level state
Applies to: marimo and Python notebook modules.
Why: mutable globals introduce hidden coupling and order-dependent behaviour.
How to fix: keep mutable state local to functions/cells and pass values explicitly.

<a id="m004"></a>
## `M004` Keep fixtures out of notebook modules
Applies to: marimo and Python notebook modules.
Why: notebook-local fixtures are harder to collect and maintain consistently.
How to fix: define fixtures in `conftest.py` or helper modules and import them.

<a id="m005"></a>
## `M005` Avoid cross-cell mutation of shared objects
Applies to: marimo and Python notebook modules.
Why: mutating shared objects across cells can make re-runs inconsistent.
How to fix: prefer immutable transformations or return new values/objects.

<a id="m006"></a>
## `M006` Avoid non-idempotent calls in cells
Applies to: marimo and Python notebook modules.
Why: non-deterministic calls make repeated execution produce different outcomes.
How to fix: add explicit seeds/inputs, isolate non-deterministic operations, or move them behind clear interfaces.

<a id="j001"></a>
## `J001` Avoid magics and shell escapes
Applies to: Jupyter notebooks (`.ipynb`) and Jupyter paired Python sources.
Why: magics and shell escapes can reduce portability and reproducibility.
How to fix: replace with explicit Python equivalents where practical.

<a id="j002"></a>
## `J002` Avoid non-idempotent calls in Jupyter code cells
Applies to: Jupyter notebooks (`.ipynb`) and Jupyter paired Python sources.
Why: Jupyter cells with non-deterministic calls can produce unstable notebook behaviour.
How to fix: seed/random-control where needed and isolate side-effecting operations.

<a id="j010"></a>
## `J010` Keep paired `.ipynb` and `.py` sources synchronised
Applies to: paired-source Jupyter workflows only.
Why: drift between paired sources creates review and maintenance confusion.
How to fix: update paired files together or disable `J010` if pairing is not required.

<a id="j011"></a>
## `J011` Require a top-of-notebook parameter/configuration cell
Applies to: Jupyter notebooks (`.ipynb`) and Jupyter paired Python sources.
Why: an explicit parameter cell improves reproducibility and automation.
How to fix: include a configuration/parameter code cell within the first few code cells.

<a id="j012"></a>
## `J012` Keep notebooks and cells reviewable
Applies to: Jupyter notebooks (`.ipynb`) and Jupyter paired Python sources.
Why: very large notebooks or long cells are harder to review and maintain.
How to fix: split notebooks and/or large cells and move heavy logic into modules.

<a id="j013"></a>
## `J013` Limit inline definitions in notebooks
Applies to: Jupyter notebooks (`.ipynb`) and Jupyter paired Python sources.
Why: excessive inline function/class definitions blur narrative and reusable logic boundaries.
How to fix: extract reusable functions/classes into modules and keep notebooks focused on orchestration.

## Candidate future rules (not implemented yet)
The following candidates are intentionally listed as optional and proportionate extensions:

- `J020` Notebook environment contract:
  require an explicit runtime/environment declaration cell (Python version, key packages, execution assumptions).
- `J021` Data input contract:
  require a clear declaration of key data inputs and expected schema/shape at notebook start.
- `J022` Side-effect boundary:
  flag notebooks that perform external writes/calls without a clearly marked side-effect section.
- `J023` Output noise budget:
  flag notebooks with very large persisted outputs that reduce reviewability.
- `M020` Secret handling guard:
  flag obvious inline secrets/tokens in notebook modules.
- `M021` Testability extraction threshold:
  nudge extraction to modules once inline complexity exceeds a configured threshold.

Recommended path: adopt candidate rules first as advisory guidance in PoC/MVP contexts, then promote selected rules to stricter enforcement where operational risk justifies it.
