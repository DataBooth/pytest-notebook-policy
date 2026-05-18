from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from .plugin import DEFAULT_RULES, EXCLUDED_DIRS, scan_file


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pytest-marimo-quality",
        description="Run Ruff and pytest-marimo semantic checks over notebook paths.",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Files or directories to check.",
    )
    parser.add_argument(
        "--skip-ruff",
        action="store_true",
        help="Skip Ruff linting and run only pytest-marimo semantic checks.",
    )
    args = parser.parse_args()

    path_args = [str(Path(path).expanduser()) for path in args.paths]

    ruff_exit_code = 0
    if not args.skip_ruff:
        ruff_exit_code = _run_ruff(path_args)

    violations = _run_marimo_checks(path_args)
    if violations:
        print("\npytest-marimo semantic violations")
        for violation in violations:
            print(f"{violation.path}:{violation.line}: {violation.code} {violation.message}")
        print(f"{len(violations)} violation(s) found.")

    if ruff_exit_code != 0 or violations:
        raise SystemExit(1)


def _run_ruff(paths: list[str]) -> int:
    command = [sys.executable, "-m", "ruff", "check", *paths]
    completed = subprocess.run(command, check=False)
    return completed.returncode


def _run_marimo_checks(paths: list[str]):
    violations = []
    select = set(DEFAULT_RULES)
    ignore: set[str] = set()

    for path in _iter_python_files(paths):
        violations.extend(scan_file(path, select=select, ignore=ignore))

    return sorted(violations, key=lambda v: (str(v.path), v.line, v.code))


def _iter_python_files(paths: list[str]):
    for raw in paths:
        path = Path(raw)
        if not path.exists():
            continue
        if path.is_file():
            if path.suffix == ".py":
                yield path.resolve()
            continue

        for candidate in path.rglob("*.py"):
            if any(part in EXCLUDED_DIRS for part in candidate.parts):
                continue
            yield candidate.resolve()
