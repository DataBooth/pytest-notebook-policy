# Backlog
## Candidate enhancements
### Optional LLM-powered advisory reporting (non-gating)
- Status: Backlog
- Goal: add an optional advisory layer that explains notebook policy findings in more depth (what, why, and suggested remediation), without changing deterministic pass/fail behaviour.
- Scope:
  - add markdown report output with enriched guidance per finding
  - keep deterministic rules as the only enforcement path in CI
  - allow opt-in local execution only (no external dependency by default)
- Notes:
  - this should remain optional and disabled by default
  - explanations should be treated as guidance, not rule truth
