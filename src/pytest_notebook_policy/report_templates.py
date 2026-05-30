from __future__ import annotations

MARKDOWN_REPORT_TEMPLATE = """## 🧪 Notebook policy report

| Metric | Value |
|---|---|
| Status | {{ status }} |
| Generated | `{{ generated_at }}` |
| Runtime | `{{ runtime_seconds }}s` |
| Files scanned | `{{ files_scanned_count }}` |
| Violations | `{{ violations_count }}` |

### 🔎 Findings

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

| Category | Count |
|---|---:|
| Key imports | `{{ imports_count }}` |
| File references | `{{ file_references_count }}` |
| HTTP requests | `{{ http_requests_count }}` |
| Data sources | `{{ data_sources_count }}` |

#### Key imports

| Import |
|---|
{% if imports %}
{% for import_name in imports %}
| `{{ import_name }}` |
{% endfor %}
{% else %}
| `(none)` |
{% endif %}

#### File references

| File | Reference |
|---|---|
{% if file_references %}
{% for reference in file_references %}
| `{{ reference.path }}` | `{{ reference.value }}` |
{% endfor %}
{% else %}
| `(none)` | `(none)` |
{% endif %}

#### HTTP requests

| File | Endpoint |
|---|---|
{% if http_requests %}
{% for request in http_requests %}
| `{{ request.path }}` | `{{ request.value }}` |
{% endfor %}
{% else %}
| `(none)` | `(none)` |
{% endif %}

#### Data sources

| File | Source |
|---|---|
{% if data_sources %}
{% for source in data_sources %}
| `{{ source.path }}` | `{{ source.value }}` |
{% endfor %}
{% else %}
| `(none)` | `(none)` |
{% endif %}

## Appendix A — Configuration

| Setting | Value |
|---|---|
| Enabled rules/prefixes | `{{ enabled_rules }}` |
| Ignored rules/prefixes | `{{ ignored_rules }}` |
| Jupyter source mode | `{{ jupyter_source }}` |
| Jupyter max code cells | `{{ max_code_cells }}` |
| Jupyter max cell lines | `{{ max_cell_lines }}` |
| Jupyter max inline definitions | `{{ max_inline_definitions }}` |
| Dependency enrichment | `{{ dependency_enrichment }}` |
| Dependency vulnerability lookup | `{{ dependency_vulnerability_lookup }}` |
| NBOM output path | `{{ nbom_output_path }}` |

## Appendix B — Scanned files

| File | Type |
|---|---|
{% if scanned_files %}
{% for scanned_file in scanned_files %}
| `{{ scanned_file.path }}` | `{{ scanned_file.filetype }}` |
{% endfor %}
{% else %}
| `(none)` | `n/a` |
{% endif %}
{% if dependency_enrichment %}

## Appendix C — Dependency enrichment

| Import | Package | Version | Licence | Homepage | Vulnerability IDs |
|---|---|---|---|---|---|
{% if dependencies %}
{% for dependency in dependencies %}
| `{{ dependency.import_name }}` | `{{ dependency.package }}` | `{{ dependency.version }}` | `{{ dependency.licence }}` | `{{ dependency.homepage }}` | `{{ dependency.vulnerability_ids }}` |
{% endfor %}
{% else %}
| `(none)` | `(none)` | `(none)` | `(none)` | `(none)` | `(none)` |
{% endif %}
{% endif %}
"""
