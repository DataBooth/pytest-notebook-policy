from __future__ import annotations

from pathlib import Path

from pytest_marimo.plugin import DEFAULT_RULES, scan_file


def _write(tmp_path: Path, name: str, source: str) -> Path:
    path = tmp_path / name
    path.write_text(source, encoding="utf-8")
    return path


def _scan(path: Path, select: set[str] | None = None, ignore: set[str] | None = None):
    return scan_file(path, select=select or set(DEFAULT_RULES), ignore=ignore or set())


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
