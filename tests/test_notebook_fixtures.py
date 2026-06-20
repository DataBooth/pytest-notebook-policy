from __future__ import annotations

from pathlib import Path

from pytest_notebook_policy.plugin import DEFAULT_RULES, scan_file

FIXTURE_ROOT = Path(__file__).parent / "fixtures"


def _scan(rel_path: str) -> set[str]:
    path = FIXTURE_ROOT / rel_path
    violations = scan_file(path, select=set(DEFAULT_RULES), ignore=set())
    return {violation.code for violation in violations}


def test_synthetic_notebook_fixtures() -> None:
    assert _scan("synthetic/good_reactive.py") == set()
    assert _scan("synthetic/bad_cross_cell_mutation.py") == {"M005"}
    assert _scan("synthetic/bad_non_idempotent.py") == {"M006"}
    assert _scan("synthetic/bad_fixture_in_notebook.py") == {"M004"}
    assert _scan("synthetic/jupyter_bad_magic.ipynb") == {"J001", "J011"}
    assert _scan("synthetic/jupyter_bad_non_idempotent.ipynb") == {"J002", "J011"}
    assert _scan("synthetic/jupyter_bad_large_notebook.ipynb") == {"J012"}
    assert _scan("synthetic/jupyter_bad_inline_defs.ipynb") == {"J013"}


def test_real_world_notebook_fixtures() -> None:
    assert _scan("real/marimo_examples_ui_file.py") == set()
    assert _scan("real/marimo_smoke_cross_cell_md.py") == set()
    assert _scan("real/gallery_matrix.py") == set()
    assert _scan("real/gallery_earthquake.py") == {"M001"}
    assert _scan("real/jupyter_running_code_v6_4_7.ipynb") == set()
    assert _scan("real/jupyter_importing_notebooks_v6_4_7.ipynb") == {"J001", "J011", "J013"}
    assert _scan("real/jupyter_connecting_qt_console_v6_4_7.ipynb") == {"J001"}
    assert _scan("real/openai_cookbook_assistants_api_overview_42bc4ed.ipynb") == {
        "J001",
        "J011",
        "J012",
        "J013",
    }
