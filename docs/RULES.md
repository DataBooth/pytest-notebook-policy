# Rule reference
This page documents each `pytest-notebook-policy` rule with concise intent and practical remediation guidance.

<a id="m001"></a>
## `M001` Prefer reactive dependencies over `on_change`
Why: callback-based state propagation can become hard to reason about in reactive notebooks.
How to fix: model dependencies explicitly so downstream cells derive values from inputs/state instead of callback side effects.

<a id="m002"></a>
## `M002` Keep test cells focused
Why: mixing assertions with setup/helper logic makes failures less clear.
How to fix: keep assertion logic in dedicated test cells and move setup/helpers into separate cells or modules.

<a id="m003"></a>
## `M003` Avoid mutable module-level state
Why: mutable globals introduce hidden coupling and order-dependent behaviour.
How to fix: keep mutable state local to functions/cells and pass values explicitly.

<a id="m004"></a>
## `M004` Keep fixtures out of notebook modules
Why: notebook-local fixtures are harder to collect and maintain consistently.
How to fix: define fixtures in `conftest.py` or helper modules and import them.

<a id="m005"></a>
## `M005` Avoid cross-cell mutation of shared objects
Why: mutating shared objects across cells can make re-runs inconsistent.
How to fix: prefer immutable transformations or return new values/objects.

<a id="m006"></a>
## `M006` Avoid non-idempotent calls in cells
Why: non-deterministic calls make repeated execution produce different outcomes.
How to fix: add explicit seeds/inputs, isolate non-deterministic operations, or move them behind clear interfaces.

<a id="j001"></a>
## `J001` Avoid magics and shell escapes
Why: magics and shell escapes can reduce portability and reproducibility.
How to fix: replace with explicit Python equivalents where practical.

<a id="j002"></a>
## `J002` Avoid non-idempotent calls in Jupyter code cells
Why: Jupyter cells with non-deterministic calls can produce unstable notebook behaviour.
How to fix: seed/random-control where needed and isolate side-effecting operations.

<a id="j010"></a>
## `J010` Keep paired `.ipynb` and `.py` sources synchronised
Why: drift between paired sources creates review and maintenance confusion.
How to fix: update paired files together or disable `J010` if pairing is not required.

<a id="j011"></a>
## `J011` Require a top-of-notebook parameter/configuration cell
Why: an explicit parameter cell improves reproducibility and automation.
How to fix: include a configuration/parameter code cell within the first few code cells.

<a id="j012"></a>
## `J012` Keep notebooks and cells reviewable
Why: very large notebooks or long cells are harder to review and maintain.
How to fix: split notebooks and/or large cells and move heavy logic into modules.

<a id="j013"></a>
## `J013` Limit inline definitions in notebooks
Why: excessive inline function/class definitions blur narrative and reusable logic boundaries.
How to fix: extract reusable functions/classes into modules and keep notebooks focused on orchestration.
