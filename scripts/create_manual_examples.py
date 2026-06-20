from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil


@dataclass(frozen=True)
class FixtureCopy:
    source_relative_path: str
    destination_relative_path: str


REPO_ROOT = Path(__file__).resolve().parents[1]

FIXTURE_COPIES = (
    FixtureCopy(
        source_relative_path="tests/fixtures/real/gallery_matrix.py",
        destination_relative_path="manual_checks/marimo/marimo_complex_good.py",
    ),
    FixtureCopy(
        source_relative_path="tests/fixtures/real/jupyter_running_code_v6_4_7.ipynb",
        destination_relative_path="manual_checks/jupyter/jupyter_complex_good.ipynb",
    ),
    FixtureCopy(
        source_relative_path="tests/fixtures/real/openai_cookbook_assistants_api_overview_42bc4ed.ipynb",
        destination_relative_path="manual_checks/jupyter/jupyter_complex_candidate.ipynb",
    ),
)


def main() -> int:
    for fixture in FIXTURE_COPIES:
        source = REPO_ROOT / fixture.source_relative_path
        destination = REPO_ROOT / fixture.destination_relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        print(f"{fixture.source_relative_path} -> {fixture.destination_relative_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
