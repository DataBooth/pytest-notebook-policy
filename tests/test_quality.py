from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from pytest_notebook_policy.plugin import Violation
from pytest_notebook_policy.quality import (
    _analyse_notebooks,
    _collect_dependency_metadata,
    _load_project_quality_defaults,
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
        "report_dependency_vulns": False,
        "report_nbom_json": None,
    }
    base.update(overrides)
    return argparse.Namespace(**base)


def test_load_project_quality_defaults_from_pyproject(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    pyproject = project / "pyproject.toml"
    pyproject.write_text(
        """
[tool.pytest.ini_options]
notebook_check_select = ["M", "J01"]
notebook_check_ignore = ["J010"]
notebook_check_jupyter_source = "paired-py"
notebook_check_jupyter_max_code_cells = "25"
notebook_check_jupyter_max_cell_lines = "110"

[tool.pytest_notebook_policy.quality]
ignore = ["M004"]
jupyter_max_inline_definitions = 6
report_md = "reports/notebook-policy.md"
report_dependency_enrichment = true
report_dependency_vulns = true
report_nbom_json = "reports/notebook-policy-nbom.json"
""",
        encoding="utf-8",
    )

    previous_cwd = Path.cwd()
    try:
        import os

        os.chdir(project)
        defaults = _load_project_quality_defaults([str(project)])
    finally:
        os.chdir(previous_cwd)
    assert defaults.select_tokens == ("M", "J01")
    assert defaults.ignore_tokens == ("J010", "M004")
    assert defaults.jupyter_source == "paired-py"
    assert defaults.max_code_cells == 25
    assert defaults.max_cell_lines == 110
    assert defaults.max_inline_definitions == 6
    assert defaults.report_md == "reports/notebook-policy.md"
    assert defaults.report_dependency_enrichment is True
    assert defaults.report_dependency_vulns is True
    assert defaults.report_nbom_json == "reports/notebook-policy-nbom.json"


def test_resolve_quality_settings_applies_cli_overrides(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "pyproject.toml").write_text(
        """
[tool.pytest_notebook_policy.quality]
select = ["M"]
ignore = ["M004"]
jupyter_source = "ipynb"
jupyter_max_code_cells = 21
jupyter_max_cell_lines = 90
jupyter_max_inline_definitions = 4
report_md = "reports/default.md"
""",
        encoding="utf-8",
    )
    notebook = project / "sample.ipynb"
    notebook.write_text('{"cells": [], "nbformat": 4, "nbformat_minor": 5}', encoding="utf-8")

    args = _namespace(
        notebook_check_select=["J"],
        notebook_check_ignore=["J010"],
        notebook_check_jupyter_source="paired-py",
        notebook_check_jupyter_max_code_cells=30,
        notebook_check_jupyter_max_cell_lines=120,
        notebook_check_jupyter_max_inline_definitions=8,
        report_md="reports/cli.md",
        report_dependency_enrichment=True,
        report_dependency_vulns=True,
        report_nbom_json="reports/nbom.json",
    )

    previous_cwd = Path.cwd()
    try:
        # _discover_pyproject_path checks cwd first.
        import os

        os.chdir(project)
        settings = _resolve_quality_settings([str(notebook)], args)
    finally:
        os.chdir(previous_cwd)

    assert settings.select == {"M", "J"}
    assert settings.ignore == {"M004", "J010"}
    assert settings.jupyter_source == "paired-py"
    assert settings.max_code_cells == 30
    assert settings.max_cell_lines == 120
    assert settings.max_inline_definitions == 8
    assert settings.report_md is not None
    assert settings.report_md.name == "cli.md"
    assert settings.report_dependency_enrichment is True
    assert settings.report_dependency_vulns is True
    assert settings.report_nbom_json is not None
    assert settings.report_nbom_json.name == "nbom.json"


def test_resolve_quality_settings_enables_enrichment_when_vulns_enabled() -> None:
    settings = _resolve_quality_settings([], _namespace(report_dependency_vulns=True))
    assert settings.report_dependency_vulns is True
    assert settings.report_dependency_enrichment is True


def test_write_markdown_report_includes_guidance(tmp_path: Path) -> None:
    report_path = tmp_path / "reports" / "policy.md"
    settings = _resolve_quality_settings([], _namespace())
    bad_file = tmp_path / "bad.py"
    bad_file.write_text(
        "import pandas\nURL='https://example.com/api'\nDATA='s3://bucket/object.parquet'\nPATH='data/input.csv'\n",
        encoding="utf-8",
    )
    violations = [
        Violation(
            path=bad_file,
            line=10,
            code="M001",
            message="Prefer reactive dependencies over on_change handlers.",
        )
    ]
    _write_markdown_report(
        report_path,
        settings=settings,
        violations=violations,
        scanned_files=[bad_file],
        started_at=datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC),
        runtime_seconds=1.23,
    )

    content = report_path.read_text(encoding="utf-8")
    assert "## 🧪 Notebook policy report" in content
    assert "| Runtime | `1.23s` |" in content
    assert "### 🔎 Findings" in content
    assert "### 🧭 Notebook surface summary" in content
    assert "#### Key imports" in content
    assert "https://example.com/api" in content
    assert "s3://bucket/object.parquet" in content
    assert "## Appendix A — Configuration" in content
    assert "## Appendix B — Scanned files" in content
    assert "bad.py" in content
    assert "[`M001`](https://github.com/DataBooth/pytest-notebook-policy/blob/main/docs/RULES.md#m001)" in content
    assert "| File | Rule | Line | What | Why this is undesirable | Suggested fix |" in content


def test_write_markdown_report_dependency_enrichment_appendix(tmp_path: Path) -> None:
    report_path = tmp_path / "reports" / "policy.md"
    settings = _resolve_quality_settings([], _namespace(report_dependency_enrichment=True))
    sample_file = tmp_path / "sample.py"
    sample_file.write_text("import json\n", encoding="utf-8")
    _write_markdown_report(
        report_path,
        settings=settings,
        violations=[],
        scanned_files=[sample_file],
        started_at=datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC),
        runtime_seconds=0.5,
    )
    content = report_path.read_text(encoding="utf-8")
    assert "## Appendix C — Dependency enrichment" in content
    assert "Vulnerability IDs" in content


def test_write_nbom_manifest(tmp_path: Path) -> None:
    nbom_path = tmp_path / "reports" / "manifest.json"
    settings = _resolve_quality_settings([], _namespace(report_dependency_enrichment=True))
    sample_file = tmp_path / "sample.py"
    sample_file.write_text("import requests\nURL='https://example.com'\n", encoding="utf-8")
    analysis = _analyse_notebooks([sample_file])
    dependencies = _collect_dependency_metadata(analysis.imports)
    _write_nbom_manifest(
        destination=nbom_path,
        settings=settings,
        violations=[],
        scanned_files=[sample_file],
        analysis=analysis,
        dependency_rows=dependencies,
        started_at=datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC),
        runtime_seconds=0.75,
    )
    content = nbom_path.read_text(encoding="utf-8")
    assert "\"schema_version\": \"0.1\"" in content
    assert "\"surface\"" in content
    assert "\"dependencies\"" in content
    assert "\"dependency_vulnerability_lookup\": false" in content
    assert "\"vulnerability_ids\": []" in content
