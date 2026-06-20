# Deterministic LLM guardrails with prek
This note consolidates recent research findings and turns them into a practical, reproducible `prek` baseline that can be used in this repository and reused across projects.

## Why this matters
Prompt instructions are probabilistic. Repository gates are deterministic.

For AI-assisted development, deterministic checks provide:
- repeatable enforcement at commit time;
- lower review burden for obvious defects;
- an auditable policy boundary in local dev and CI.

## Key findings from the research
Across the reviewed material, the same pattern appears repeatedly:
1. Prompt-only controls are not enough.
2. Schema/format validation catches structure issues, not semantic correctness.
3. Layered gates work best:
   - fast local checks (`prek`);
   - CI enforcement;
   - optional semantic/domain-specific validators.

## Deterministic check categories
Recommended categories for an AI-assisted repo baseline:

1. Encoding and text integrity
   - UTF-8 validity
   - control/invisible character checks
   - optional BOM policy

2. Repository hygiene
   - merge-conflict markers
   - private key/secret patterns
   - trailing whitespace and EOF consistency
   - YAML/JSON/TOML syntax validity

3. Code quality gates
   - linting
   - tests (targeted + full where appropriate)
   - optional type checks

4. Policy-pattern checks (project specific)
   - language-mixing heuristics (for example SQL embedded in Python string literals)
   - architecture-specific anti-patterns
   - allow-listed exceptions with explicit inline annotation

5. Release/documentation integrity
   - packaging checks
   - docs build and link checks (prepublish + strict variants)

## Current state in this repository
This repository already has a strong deterministic base with `prek`:
- `check-merge-conflict`
- `detect-private-key`
- `check-json`
- `check-yaml`
- `check-toml`
- `text-safety-check`
- `python-sql-literal-check`
- `ruff-check`
- `pytest-tests`
- `pytest-report-regressions`

And supporting `just` commands:
- `just hooks-install`
- `just hooks-run`
- `just qa`
- docs and release validation recipes

This now includes a dedicated “AI safety” hook layer for text-integrity and language-mix checks.

## Suggested next additions for this repo
Priority order after the first safety baseline:

1. Tune and measure false positives
   - track `text-safety-check` and `python-sql-literal-check` hit rates;
   - tighten/relax heuristics using explicit examples.

2. Add CI enforcement for all hooks
   - run `uv run prek run --all-files` in CI as a non-bypassable gate.

3. Add explicit waiver policy
   - standardise allow markers and require rationale in review for each waiver.

4. Extend project-specific patterns
   - add further deterministic checks for policy-specific anti-patterns as needed.

## Reproducible cross-project strategy
To use this consistently across projects, standardise on a shared “guardrail pack”.

### Model
Use a two-part standard:
1. Shared hook implementation
2. Shared policy configuration

### Recommended implementation patterns
Option A (most portable): shared hooks repository
- Create a central hooks repo containing:
  - scripts/check_text_safety.py
  - scripts/check_language_mix.py
  - `.pre-commit-hooks.yaml` (compatible with `prek`)
- In each project `prek.toml`, reference the shared repo and pin a tag/commit.

Option B (best for Python-heavy orgs): internal Python package
- Publish `org-llm-guardrails` with console entry points.
- Each project installs it in dev dependencies and uses `repo = "local"` hooks calling the package CLI.

Option C (bootstrap support): template synchronisation
- Maintain a template `prek.toml` + scripts bundle.
- Use a small sync script to roll baseline updates across repos.

In practice, A or B plus C gives best reproducibility.

## Governance and rollout
Use phased enforcement:
1. Observe mode
   - run checks in CI, report warnings, tune false positives.
2. Soft fail on high-risk categories
   - secrets, invalid encoding, conflict markers.
3. Full blocking
   - enforce mature checks at pre-commit and CI levels.

For every non-trivial heuristic, define:
- failure message;
- allow-list mechanism;
- owner and review cadence.

## Minimal baseline blueprint
Every project should have:
- `prek.toml` with:
  - hygiene checks
  - lint/test checks
  - AI safety hooks
- `just hooks-install` and `just hooks-run`
- CI job that runs `prek run --all-files`
- brief policy doc describing:
  - what is blocked;
  - what can be waived;
  - who approves waivers.

## Research references
- https://www.iamraghuveer.com/posts/pre-commit-hooks-agentic-output-validation/
- https://blog.merrilin.ai/engineering/2026/reining-in-ai-with-precommit/
- https://dev.to/sjh9714/i-built-a-deterministic-ci-firewall-for-ai-generated-pull-requests-4o3c
- https://agentpatterns.ai/verification/deterministic-guardrails/
- https://palakorn.com/blog/llm-evaluation-guardrails-production/
- https://www.glukhov.org/llm-performance/benchmarks/llm-structured-output-validation-python/
- https://fordelstudios.com/research/structured-outputs-production-systems
- https://dev.to/zendev2112/prompts-arent-enough-enforcing-hard-constraints-on-llm-output-2hpo
- https://qaskills.sh/blog/llm-guardrails-testing-guide-2026

