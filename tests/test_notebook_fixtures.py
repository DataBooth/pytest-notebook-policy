from __future__ import annotations

from pathlib import Path

from pytest_marimo.plugin import DEFAULT_RULES, scan_file

FIXTURE_ROOT = Path(__file__).parent / "fixtures"


def _scan(rel_path: str) -> set[str]:
    path = FIXTURE_ROOT / rel_path
    violations = scan_file(path, select=set(DEFAULT_RULES), ignore=set())
    return {violation.code for violation in violations}


def test_synthetic_notebook_fixtures() -> None:
    assert _scan("synthetic/good_reactive.py") == set()
    assert _scan("synthetic/bad_cross_cell_mutation.py") == {"M005"}
    assert _scan("synthetic/bad_non_idempotent.py") == {"M006"}


def test_real_world_notebook_fixtures() -> None:
    assert _scan("real/marimo_examples_ui_file.py") == set()
    assert _scan("real/marimo_smoke_cross_cell_md.py") == set()
    assert _scan("real/gallery_matrix.py") == set()
    assert _scan("real/gallery_earthquake.py") == {"M001"}
