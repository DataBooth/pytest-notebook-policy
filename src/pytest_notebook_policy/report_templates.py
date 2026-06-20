MARKDOWN_REPORT_TEMPLATE = """## 🧪 Notebook policy report
This report was generated to provide a deterministic notebook quality snapshot for reproducibility, maintainability, and operational confidence.

### Executive summary
{{ exec_summary_text }}

| Metric | Value |
|---|---|
| Status | {{ status }} |
| Generated | `{{ generated_at }}` |
| Runtime | `{{ runtime_seconds }}s` |
| Files scanned | `{{ files_scanned }}` |
| Violations | `{{ violations_count }}` |

### 🔎 Findings
This section lists rule-level findings with concise rationale and practical remediation guidance.

{% if findings %}
| File | Rule | Line | What | Why this is undesirable | Suggested fix |
|---|---|---:|---|---|---|
{% for finding in findings %}
| `{{ finding.path }}` | {{ finding.rule_link }} | `{{ finding.line }}` | {{ finding.message }} | {{ finding.why }} | {{ finding.remediation }} |
{% endfor %}
{% else %}
No notebook policy violations were found.
{% endif %}

### 🧭 Notebook surface summary
This section summarises observable notebook touchpoints to support review and downstream governance workflows.

| Category | Count |
|---|---:|
| Key imports | `{{ imports_count }}` |
| File references | `{{ file_references_count }}` |
| HTTP requests | `{{ http_requests_count }}` |
| Data sources | `{{ data_sources_count }}` |

#### Key imports
These imports were observed across scanned notebooks.

| Import |
|---|
{% if imports %}
{% for name in imports %}
| `{{ name }}` |
{% endfor %}
{% else %}
| `(none)` |
{% endif %}

#### File references
Potential file/path references observed in notebook source literals.

| File | Reference |
|---|---|
{% if file_references %}
{% for observed in file_references %}
| `{{ observed.path }}` | `{{ observed.value }}` |
{% endfor %}
{% else %}
| `(none)` | `(none)` |
{% endif %}

#### HTTP requests
Potential HTTP endpoints observed in notebook source literals.

| File | Endpoint |
|---|---|
{% if http_requests %}
{% for observed in http_requests %}
| `{{ observed.path }}` | `{{ observed.value }}` |
{% endfor %}
{% else %}
| `(none)` | `(none)` |
{% endif %}

#### Data sources
Potential data source URIs observed in notebook source literals.

| File | Source |
|---|---|
{% if data_sources %}
{% for observed in data_sources %}
| `{{ observed.path }}` | `{{ observed.value }}` |
{% endfor %}
{% else %}
| `(none)` | `(none)` |
{% endif %}

## Appendix A — Configuration
This appendix captures the effective policy configuration used for this report run.

| Setting | Value |
|---|---|
| Enabled rules/prefixes | `{{ enabled_rules }}` |
| Ignored rules/prefixes | `{{ ignored_rules }}` |
| Jupyter source mode | `{{ jupyter_source }}` |
| Jupyter max code cells | `{{ max_code_cells }}` |
| Jupyter max cell lines | `{{ max_cell_lines }}` |
| Jupyter max inline definitions | `{{ max_inline_definitions }}` |
| Dependency enrichment | `{{ dependency_enrichment_enabled }}` |
| NBOM output path | `{{ nbom_output_path }}` |

## Appendix B — Scanned files
This appendix lists all notebook files included in the report run.

| File | Type |
|---|---|
{% if scanned_files %}
{% for scanned in scanned_files %}
| `{{ scanned.path }}` | `{{ scanned.kind }}` |
{% endfor %}
{% else %}
| `(none)` | `n/a` |
{% endif %}

## Appendix C — NBOM alignment
This appendix summarises NBOM JSON linkage so markdown and machine-readable outputs can be reviewed together.

| NBOM field | Value |
|---|---|
| NBOM requested | `{{ nbom_requested }}` |
| NBOM output path | `{{ nbom_output_path }}` |
| Files scanned | `{{ files_scanned }}` |
| Violations | `{{ violations_count }}` |
| Imports observed | `{{ imports_count }}` |
| File references observed | `{{ file_references_count }}` |
| HTTP requests observed | `{{ http_requests_count }}` |
| Data sources observed | `{{ data_sources_count }}` |
| Dependencies recorded | `{{ dependency_count }}` |

{% if dependency_enrichment_enabled %}
## Appendix D — Dependency enrichment
This appendix provides import-to-package metadata enrichment for dependency visibility.

| Import | Package | Version | Licence | Homepage |
|---|---|---|---|---|
{% if dependencies %}
{% for dependency in dependencies %}
| `{{ dependency.import_name }}` | `{{ dependency.package }}` | `{{ dependency.version }}` | `{{ dependency.licence }}` | `{{ dependency.homepage }}` |
{% endfor %}
{% else %}
| `(none)` | `(none)` | `(none)` | `(none)` | `(none)` |
{% endif %}
{% endif %}
"""
