from __future__ import annotations

from pathlib import Path
import shutil


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_PATHS = ("build", "dist")


def _remove_if_exists(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path)
        return
    path.unlink()


def main() -> int:
    for relative in BUILD_PATHS:
        _remove_if_exists(REPO_ROOT / relative)

    for egg_info in REPO_ROOT.glob("*.egg-info"):
        _remove_if_exists(egg_info)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
