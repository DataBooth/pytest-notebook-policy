from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlopen

from pytest_notebook_policy.plugin import DEFAULT_RULES, scan_file


@dataclass(frozen=True)
class FixtureSource:
    filename: str
    url: str


FIXTURE_SOURCES = (
    FixtureSource(
        filename="marimo_examples_ui_file.py",
        url="https://raw.githubusercontent.com/marimo-team/marimo/main/examples/ui/file.py",
    ),
    FixtureSource(
        filename="marimo_smoke_cross_cell_md.py",
        url=(
            "https://raw.githubusercontent.com/marimo-team/marimo/main/"
            "marimo/_smoke_tests/markdown/cross_cell_md.py"
        ),
    ),
    FixtureSource(
        filename="gallery_matrix.py",
        url="https://raw.githubusercontent.com/marimo-team/gallery-examples/main/notebooks/math/matrix.py",
    ),
    FixtureSource(
        filename="gallery_earthquake.py",
        url="https://raw.githubusercontent.com/marimo-team/gallery-examples/main/notebooks/geo/earthquake.py",
    ),
    FixtureSource(
        filename="jupyter_running_code_v6_4_7.ipynb",
        url=(
            "https://raw.githubusercontent.com/jupyter/notebook/v6.4.7/"
            "docs/source/examples/Notebook/Running%20Code.ipynb"
        ),
    ),
    FixtureSource(
        filename="jupyter_importing_notebooks_v6_4_7.ipynb",
        url=(
            "https://raw.githubusercontent.com/jupyter/notebook/v6.4.7/"
            "docs/source/examples/Notebook/Importing%20Notebooks.ipynb"
        ),
    ),
    FixtureSource(
        filename="jupyter_connecting_qt_console_v6_4_7.ipynb",
        url=(
            "https://raw.githubusercontent.com/jupyter/notebook/v6.4.7/"
            "docs/source/examples/Notebook/Connecting%20with%20the%20Qt%20Console.ipynb"
        ),
    ),
    FixtureSource(
        filename="openai_cookbook_assistants_api_overview_42bc4ed.ipynb",
        url=(
            "https://raw.githubusercontent.com/openai/openai-cookbook/"
            "42bc4ed33a2d1ee308c1f614c073f1b5f760061b/examples/"
            "Assistants_API_overview_python.ipynb"
        ),
    ),
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "real"


def _download_fixture(source: FixtureSource) -> None:
    destination = REAL_FIXTURE_DIR / source.filename
    with urlopen(source.url) as response:  # noqa: S310
        content = response.read()
    destination.write_bytes(content)


def _report_rule_codes(source: FixtureSource) -> str:
    fixture_path = REAL_FIXTURE_DIR / source.filename
    violations = scan_file(fixture_path, select=set(DEFAULT_RULES), ignore=set())
    codes = sorted({violation.code for violation in violations})
    return f"{source.filename}: {codes}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh real notebook fixtures from pinned URLs and print observed rule codes."
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Skip downloads and only print currently observed rule-code sets.",
    )
    args = parser.parse_args()

    REAL_FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

    if not args.report_only:
        for source in FIXTURE_SOURCES:
            _download_fixture(source)

    for source in FIXTURE_SOURCES:
        print(_report_rule_codes(source))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
