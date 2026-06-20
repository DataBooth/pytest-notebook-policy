# Roadmap
This document captures likely next steps for `pytest-notebook-policy` after the current release baseline.

## Near-term priorities
- Finalise report UX:
  - findings-first layout
  - appendix-style configuration and scanned file sections
  - cleaner multi-notebook summaries
- Expand deterministic notebook surface reporting:
  - key imports
  - file references
  - HTTP endpoints
  - data source hints
- Improve docs for report interpretation and policy tuning workflows.

## Immediate easy wins (prioritised)
1. Improve docs for report interpretation and policy tuning workflows.
   - Why first: highest user impact for lowest implementation effort.
2. Tighten prek and CI quality gates around report regressions.
   - Why second: mostly workflow configuration with fast confidence gains.
3. Expand example notebooks and fixture coverage for real-world edge cases.
   - Why third: incremental additions that improve trust and regression safety.
4. Finalise cleaner multi-notebook report summaries.
   - Why fourth: contained UX improvement with clear value for teams scanning many notebooks.

## Dependency and supply-chain visibility
- Add opt-in dependency enrichment for report output:
  - import-to-package mapping
  - package version and licence metadata
  - optional advisory/vulnerability integration behind explicit flags
- Evaluate integration options for package quality/security intelligence providers, subject to terms of service and stable API availability.

## NBOM/SBOM direction
- Define a notebook usage manifest (NBOM-like) that captures:
  - notebook files scanned
  - imports observed
  - external touchpoints
  - dependency correlation
- Evaluate interoperability with CycloneDX-oriented Python tooling for broader SBOM workflows.

## Policy engine evolution
- Add deeper static analysis patterns while remaining deterministic and fast.
- Improve rule-level configuration granularity and report drill-down detail.
- Keep optional advisory features non-gating by default.
- Add a local LLM Lite notebook-style assessor (optional advisory mode):
  - runs locally for style/narrative/cohesion recommendations
  - never auto-applies changes
  - non-gating by default, designed as guidance/coaching
  - complements deterministic rules with human-readable improvement suggestions

## Release and ecosystem readiness
- Tighten prek and CI quality gates around report regressions.
- Publish and maintain clear release notes and upgrade guidance.
- Expand example notebooks and fixture coverage for real-world edge cases.
