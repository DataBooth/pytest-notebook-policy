from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from pytest_notebook_policy.plugin import Violation
from pytest_notebook_policy.quality import (
    NotebookAnalysis,
    Observed,
    _resolve_quality_settings,
    _write_markdown_report,
    _write_nbom_manifest,
)


def _namespace(**overrides: object) -> argparse.Namespace:
    base: dict[str, object] = {
        "notebook_check_select": [],
        "notebook_check_ignore": [],
        "notebook_check_jupyter_source": None,
        "notebook_check_jupyter_max_code_cells": None,
        "notebook_check_jupyter_max_cell_lines": None,
        "notebook_check_jupyter_max_inline_definitions": None,
        "report_md": None,
        "report_dependency_enrichment": False,
        "report_nbom_json": None,
    }
    base.update(overrides)
    return argparse.Namespace(**base)


def test_markdown_report_contract_structure_is_stable(tmp_path: Path) -> None:
    report_path = tmp_path / "reports" / "policy.md"
    scanned_file = tmp_path / "sample.py"
    scanned_file.write_text("import requests\n", encoding="utf-8")
    settings = _resolve_quality_settings([], _namespace(report_dependency_enrichment=True))
    violations = [
        Violation(
            path=scanned_file,
            line=3,
            code="M001",
            message="Prefer reactive dependencies over on_change handlers.",
        )
    ]

    _write_markdown_report(
        report_path,
        settings=settings,
        violations=violations,
        scanned_files=[scanned_file],
        started_at=datetime(2026, 6, 1, 0, 0, 0, tzinfo=UTC),
        runtime_seconds=1.11,
    )

    content = report_path.read_text(encoding="utf-8")
    required_sections = [
        "## 🧪 Notebook policy report",
        "### Executive summary",
        "### 🔎 Findings",
        "### 🧭 Notebook surface summary",
        "## Appendix A — Configuration",
        "## Appendix B — Scanned files",
        "## Appendix C — NBOM alignment",
        "## Appendix D — Dependency enrichment",
    ]
    for section in required_sections:
        assert section in content
    section_positions = [content.index(section) for section in required_sections]
    assert section_positions == sorted(section_positions)
    assert "| File | Rule | Line | What | Why this is undesirable | Suggested fix |" in content
    assert "[`M001`](https://github.com/DataBooth/pytest-notebook-policy/blob/main/docs/RULES.md#m001)" in content
    assert "| Runtime | `1.11s` |" in content
    assert "deterministic notebook quality snapshot" in content


def test_markdown_report_dependency_appendix_is_optional(tmp_path: Path) -> None:
    report_path = tmp_path / "reports" / "policy.md"
    scanned_file = tmp_path / "sample.py"
    scanned_file.write_text("x = 1\n", encoding="utf-8")
    settings = _resolve_quality_settings([], _namespace(report_dependency_enrichment=False))

    _write_markdown_report(
        report_path,
        settings=settings,
        violations=[],
        scanned_files=[scanned_file],
        started_at=datetime(2026, 6, 1, 0, 0, 0, tzinfo=UTC),
        runtime_seconds=0.25,
    )

    content = report_path.read_text(encoding="utf-8")
    assert "## Appendix C — NBOM alignment" in content
    assert "## Appendix D — Dependency enrichment" not in content
    assert "| Dependency enrichment | `False` |" in content


def test_nbom_manifest_contract_schema_is_stable(tmp_path: Path) -> None:
    nbom_path = tmp_path / "reports" / "manifest.json"
    scanned_file = tmp_path / "sample.ipynb"
    scanned_file.write_text('{"cells": [], "nbformat": 4, "nbformat_minor": 5}', encoding="utf-8")
    settings = _resolve_quality_settings([], _namespace(report_dependency_enrichment=True))
    analysis = NotebookAnalysis(
        imports={"requests"},
        file_references={Observed(path=scanned_file, value="data/input.csv")},
        http_requests={Observed(path=scanned_file, value="https://example.com/api")},
        data_sources={Observed(path=scanned_file, value="s3://bucket/object.parquet")},
    )
    violations = [
        Violation(
            path=scanned_file,
            line=1,
            code="J011",
            message="Add a top-of-notebook parameter/configuration cell.",
        )
    ]
    dependency_rows = [
        ("requests", "requests", "2.32.0", "Apache-2.0", "https://requests.readthedocs.io")
    ]

    _write_nbom_manifest(
        destination=nbom_path,
        settings=settings,
        violations=violations,
        scanned_files=[scanned_file],
        analysis=analysis,
        dependency_rows=dependency_rows,
        started_at=datetime(2026, 6, 1, 0, 0, 0, tzinfo=UTC),
        runtime_seconds=0.5,
    )

    manifest = json.loads(nbom_path.read_text(encoding="utf-8"))
    assert set(manifest) == {
        "schema_version",
        "generated_at",
        "runtime_seconds",
        "tool",
        "settings",
        "files",
        "violations",
        "surface",
        "dependencies",
        "summary",
    }
    assert manifest["schema_version"] == "0.1"
    assert manifest["tool"] == "pytest-notebook-policy"
    assert manifest["summary"]["violations"] == 1
    assert manifest["summary"]["dependencies"] == 1
    assert manifest["dependencies"][0]["import"] == "requests"
    assert "http_requests" in manifest["dependencies"][0]["capabilities"]
