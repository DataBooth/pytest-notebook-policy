from __future__ import annotations
import json

from pathlib import Path
import pytest

from pytest_notebook_policy.plugin import DEFAULT_RULES, scan_file


def _write(tmp_path: Path, name: str, source: str) -> Path:
    path = tmp_path / name
    path.write_text(source, encoding="utf-8")
    return path


def _scan(
    path: Path,
    select: set[str] | None = None,
    ignore: set[str] | None = None,
    jupyter_source: str = "ipynb",
    max_code_cells: int = 20,
    max_cell_lines: int = 80,
    max_inline_definitions: int = 3,
):
    return scan_file(
        path,
        select=select or set(DEFAULT_RULES),
        ignore=ignore or set(),
        jupyter_source=jupyter_source,
        max_code_cells=max_code_cells,
        max_cell_lines=max_cell_lines,
        max_inline_definitions=max_inline_definitions,
    )


def _write_ipynb(tmp_path: Path, name: str, cells: list[dict]) -> Path:
    path = tmp_path / name
    normalised_cells: list[dict] = []
    for index, cell in enumerate(cells):
        normalised_cell = dict(cell)
        normalised_cell.setdefault("id", f"cell-{index:04d}")
        normalised_cells.append(normalised_cell)
    notebook = {"cells": normalised_cells, "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
    path.write_text(json.dumps(notebook), encoding="utf-8")
    return path


def test_non_marimo_file_is_ignored(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "test_plain.py",
        """
def test_ok():
    assert 1 == 1
""",
    )
    assert _scan(path) == []


def test_flags_on_change_handler(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "test_notebook.py",
        """
import marimo

app = marimo.App()

@app.cell
def _():
    slider = marimo.ui.slider(1, 10, on_change=lambda value: value)
    return slider
""",
    )
    codes = [violation.code for violation in _scan(path)]
    assert "M001" in codes


def test_flags_mixed_test_and_setup_in_cell(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "test_mixed.py",
        """
import marimo

app = marimo.App()

@app.cell
def _():
    x = 1

    def test_value():
        assert x == 1

    return test_value
""",
    )
    codes = [violation.code for violation in _scan(path)]
    assert "M002" in codes


def test_flags_module_level_state(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "test_state.py",
        """
import marimo

app = marimo.App()
cache = {}

@app.cell
def _():
    return
""",
    )
    codes = [violation.code for violation in _scan(path)]
    assert "M003" in codes


def test_flags_fixture_inside_notebook(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "test_fixture.py",
        """
import marimo
import pytest

app = marimo.App()

@pytest.fixture
def value():
    return 1

@app.cell
def _():
    return
""",
    )
    codes = [violation.code for violation in _scan(path)]
    assert "M004" in codes


def test_select_and_ignore_filters_rules(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "test_filters.py",
        """
import marimo

app = marimo.App()

@app.cell
def _():
    slider = marimo.ui.slider(1, 10, on_change=lambda value: value)
    return slider
""",
    )
    only_m001 = _scan(path, select={"M001"}, ignore=set())
    assert {violation.code for violation in only_m001} == {"M001"}

    ignored = _scan(path, select={"M001"}, ignore={"M001"})
    assert ignored == []


def test_flags_cross_cell_mutation(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "test_mutation.py",
        """
import marimo

app = marimo.App()

@app.cell
def _():
    values = [1, 2]
    return (values,)

@app.cell
def _(values):
    values.append(3)
    return
""",
    )
    codes = [violation.code for violation in _scan(path)]
    assert "M005" in codes


def test_flags_non_idempotent_call(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "test_non_idempotent.py",
        """
import marimo
import random

app = marimo.App()

@app.cell
def _():
    value = random.random()
    return (value,)
""",
    )
    codes = [violation.code for violation in _scan(path)]
    assert "M006" in codes


def test_flags_jupyter_magic_and_shell_usage(tmp_path: Path) -> None:
    path = _write_ipynb(
        tmp_path,
        "test_notebook.ipynb",
        cells=[
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": ["%matplotlib inline\n", "value = 1\n"],
            }
        ],
    )
    codes = {violation.code for violation in _scan(path)}
    assert "J001" in codes


def test_flags_jupyter_non_idempotent_call(tmp_path: Path) -> None:
    path = _write_ipynb(
        tmp_path,
        "test_non_idempotent.ipynb",
        cells=[
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": ["import random\n", "value = random.random()\n"],
            }
        ],
    )
    codes = {violation.code for violation in _scan(path)}
    assert "J002" in codes


def test_j010_flags_missing_paired_script(tmp_path: Path) -> None:
    path = _write_ipynb(
        tmp_path,
        "sync_target.ipynb",
        cells=[
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": ["x = 1\n"],
            }
        ],
    )
    codes = {violation.code for violation in _scan(path, select={"J010"}, ignore=set())}
    assert "J010" in codes


def test_j010_passes_when_ipynb_and_script_match(tmp_path: Path) -> None:
    path = _write_ipynb(
        tmp_path,
        "paired.ipynb",
        cells=[
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": ["x = 1\n"],
            }
        ],
    )
    paired_script = tmp_path / "paired.py"
    paired_script.write_text(
        """# ---\n# jupyter:\n#   jupytext:\n#     formats: ipynb,py:percent\n# ---\n\n# %%\nx = 1\n""",
        encoding="utf-8",
    )

    violations = _scan(path, select={"J010"}, ignore=set())
    assert violations == []


def test_paired_py_source_mode_uses_paired_script_cells_for_j_rules(tmp_path: Path) -> None:
    pytest.importorskip("jupytext")
    path = _write_ipynb(
        tmp_path,
        "source_switch.ipynb",
        cells=[
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": ["%matplotlib inline\n", "value = 1\n"],
            }
        ],
    )
    paired_script = tmp_path / "source_switch.py"
    paired_script.write_text(
        """# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
# ---

# %%
value = 1
""",
        encoding="utf-8",
    )

    ipynb_scan = _scan(path, select={"J001"}, ignore=set(), jupyter_source="ipynb")
    paired_scan = _scan(path, select={"J001"}, ignore=set(), jupyter_source="paired-py")

    assert {violation.code for violation in ipynb_scan} == {"J001"}
    assert paired_scan == []


def test_paired_py_source_mode_falls_back_to_ipynb_when_no_pair(tmp_path: Path) -> None:
    path = _write_ipynb(
        tmp_path,
        "no_pair.ipynb",
        cells=[
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": ["%time value = 1\n"],
            }
        ],
    )

    violations = _scan(path, select={"J001"}, ignore=set(), jupyter_source="paired-py")
    assert {violation.code for violation in violations} == {"J001"}


def test_j011_flags_when_no_parameter_cell_near_top(tmp_path: Path) -> None:
    path = _write_ipynb(
        tmp_path,
        "missing_params.ipynb",
        cells=[
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": ["import pandas as pd\n"],
            },
            {
                "cell_type": "code",
                "execution_count": 2,
                "metadata": {},
                "outputs": [],
                "source": ["df = pd.DataFrame({'x': [1, 2, 3]})\n"],
            },
        ],
    )
    codes = {violation.code for violation in _scan(path, select={"J011"}, ignore=set())}
    assert "J011" in codes


def test_j011_passes_with_parameter_cell_near_top(tmp_path: Path) -> None:
    path = _write_ipynb(
        tmp_path,
        "with_params.ipynb",
        cells=[
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": ["params = {'seed': 42, 'dataset': 'train'}\n"],
            },
            {
                "cell_type": "code",
                "execution_count": 2,
                "metadata": {},
                "outputs": [],
                "source": ["print(params['dataset'])\n"],
            },
        ],
    )
    assert _scan(path, select={"J011"}, ignore=set()) == []


def test_j012_flags_large_notebook(tmp_path: Path) -> None:
    cells = [
        {
            "cell_type": "code",
            "execution_count": i + 1,
            "metadata": {},
            "outputs": [],
            "source": [f"value_{i} = {i}\n"],
        }
        for i in range(21)
    ]
    path = _write_ipynb(tmp_path, "large_notebook.ipynb", cells=cells)
    codes = {violation.code for violation in _scan(path, select={"J012"}, ignore=set())}
    assert "J012" in codes


def test_j012_respects_custom_max_code_cells_threshold(tmp_path: Path) -> None:
    path = _write_ipynb(
        tmp_path,
        "small_notebook.ipynb",
        cells=[
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": ["x = 1\n"],
            },
            {
                "cell_type": "code",
                "execution_count": 2,
                "metadata": {},
                "outputs": [],
                "source": ["y = 2\n"],
            },
        ],
    )
    assert _scan(path, select={"J012"}, ignore=set()) == []
    codes = {
        violation.code
        for violation in _scan(path, select={"J012"}, ignore=set(), max_code_cells=1)
    }
    assert codes == {"J012"}


def test_j013_flags_excessive_inline_definitions(tmp_path: Path) -> None:
    path = _write_ipynb(
        tmp_path,
        "inline_defs.ipynb",
        cells=[
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": ["def a():\n", "    return 1\n"],
            },
            {
                "cell_type": "code",
                "execution_count": 2,
                "metadata": {},
                "outputs": [],
                "source": ["def b():\n", "    return 2\n"],
            },
            {
                "cell_type": "code",
                "execution_count": 3,
                "metadata": {},
                "outputs": [],
                "source": ["def c():\n", "    return 3\n"],
            },
            {
                "cell_type": "code",
                "execution_count": 4,
                "metadata": {},
                "outputs": [],
                "source": ["class D:\n", "    pass\n"],
            },
        ],
    )
    codes = {violation.code for violation in _scan(path, select={"J013"}, ignore=set())}
    assert "J013" in codes


def test_j013_respects_custom_inline_definition_threshold(tmp_path: Path) -> None:
    path = _write_ipynb(
        tmp_path,
        "few_inline_defs.ipynb",
        cells=[
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": ["def a():\n", "    return 1\n"],
            },
            {
                "cell_type": "code",
                "execution_count": 2,
                "metadata": {},
                "outputs": [],
                "source": ["def b():\n", "    return 2\n"],
            },
        ],
    )
    assert _scan(path, select={"J013"}, ignore=set()) == []
    codes = {
        violation.code
        for violation in _scan(
            path, select={"J013"}, ignore=set(), max_inline_definitions=1
        )
    }
    assert codes == {"J013"}
