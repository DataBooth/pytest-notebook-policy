from __future__ import annotations

import argparse
import ast
import importlib.metadata as importlib_metadata
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import time
import tomllib

from .plugin import (
    DEFAULT_RULES,
    EXCLUDED_DIRS,
    JUPYTER_MAX_CELL_LINES,
    JUPYTER_MAX_CODE_CELLS,
    JUPYTER_MAX_INLINE_DEFINITIONS,
    JUPYTER_SOURCE_CHOICES,
    Violation,
    scan_file,
)

RULE_GUIDANCE: dict[str, tuple[str, str]] = {
    "M001": (
        "Reactive dataflow is easier to reason about than callback-style imperative updates.",
        "Prefer derived-cell dependencies over `on_change` callbacks for state propagation.",
    ),
    "M002": (
        "Mixing assertions and setup logic in one cell makes failures harder to diagnose.",
        "Keep test assertions in focused test cells and move helpers/setup into separate cells/modules.",
    ),
    "M003": (
        "Mutable module-level state can introduce hidden coupling across cells.",
        "Move mutable state inside cells/functions and return explicit values between cells.",
    ),
    "M004": (
        "Notebook-local fixtures are harder to collect and maintain consistently.",
        "Define fixtures in `conftest.py` or helper modules and import them where needed.",
    ),
    "M005": (
        "Cross-cell mutation creates order-dependent behaviour and subtle bugs.",
        "Return new objects instead of mutating shared inputs or global mutable values.",
    ),
    "M006": (
        "Non-idempotent calls make notebook re-runs produce inconsistent results.",
        "Gate non-idempotent calls behind explicit inputs/seeds or isolate them from deterministic logic.",
    ),
    "J001": (
        "Magics and shell escapes often reduce portability and reproducibility.",
        "Replace magics/shell escapes with explicit Python equivalents where possible.",
    ),
    "J002": (
        "Non-idempotent calls in notebook cells make repeated runs unstable.",
        "Use explicit seeds/inputs or isolate non-deterministic operations behind controlled parameters.",
    ),
    "J010": (
        "Paired sources drift when code changes are not synchronised.",
        "Keep `.ipynb` and paired `.py` files in sync, or disable `J010` if pairing is not required.",
    ),
    "J011": (
        "A clear parameter cell improves reproducibility and automation.",
        "Add a top-of-notebook configuration/parameter code cell within the first three code cells.",
    ),
    "J012": (
        "Large notebooks or very long cells are harder to review and maintain.",
        "Split notebooks/cells into smaller units and move complex logic into importable modules.",
    ),
    "J013": (
        "Too many inline definitions blur notebook narrative and reusable logic boundaries.",
        "Extract reusable functions/classes into modules and keep notebooks focused on orchestration.",
    ),
}

RULES_DOC_URL_BASE = "https://github.com/DataBooth/pytest-notebook-policy/blob/main/docs/RULES.md"
HTTP_PATTERN = re.compile(r"^https?://", re.IGNORECASE)
DATA_SOURCE_PREFIXES = (
    "s3://",
    "gs://",
    "abfs://",
    "hdfs://",
    "postgres://",
    "postgresql://",
    "mysql://",
    "sqlite://",
)
FILE_HINT_SUFFIXES = (
    ".csv",
    ".json",
    ".parquet",
    ".xlsx",
    ".xls",
    ".txt",
    ".yaml",
    ".yml",
    ".toml",
    ".db",
    ".sql",
    ".pkl",
    ".pickle",
    ".ipynb",
    ".py",
)


@dataclass(frozen=True)
class QualityDefaults:
    select_tokens: tuple[str, ...] = ()
    ignore_tokens: tuple[str, ...] = ()
    jupyter_source: str | None = None
    max_code_cells: int | None = None
    max_cell_lines: int | None = None
    max_inline_definitions: int | None = None
    report_md: str | None = None
    report_dependency_enrichment: bool | None = None
    report_nbom_json: str | None = None


@dataclass(frozen=True)
class QualitySettings:
    select: set[str]
    ignore: set[str]
    jupyter_source: str
    max_code_cells: int
    max_cell_lines: int
    max_inline_definitions: int
    report_md: Path | None
    report_dependency_enrichment: bool
    report_nbom_json: Path | None


@dataclass(frozen=True)
class Observed:
    path: Path
    value: str


@dataclass(frozen=True)
class NotebookAnalysis:
    imports: set[str]
    file_references: set[Observed]
    http_requests: set[Observed]
    data_sources: set[Observed]


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pytest-notebook-quality",
        description="Run Ruff and notebook policy checks over notebook paths.",
    )
    parser.add_argument("paths", nargs="+", help="Files or directories to check.")
    parser.add_argument(
        "--skip-ruff",
        action="store_true",
        help="Skip Ruff linting and run only notebook policy checks.",
    )
    parser.add_argument(
        "--notebook-check-select",
        action="append",
        default=[],
        metavar="RULE",
        help="Rule code or prefix to enable (repeatable, e.g. M001, J01).",
    )
    parser.add_argument(
        "--notebook-check-ignore",
        action="append",
        default=[],
        metavar="RULE",
        help="Rule code or prefix to ignore (repeatable, e.g. J010).",
    )
    parser.add_argument(
        "--notebook-check-jupyter-source",
        action="store",
        choices=JUPYTER_SOURCE_CHOICES,
        default=None,
        metavar="SOURCE",
        help="Source used for Jupyter rule checks: ipynb or paired-py.",
    )
    parser.add_argument(
        "--notebook-check-jupyter-max-code-cells",
        action="store",
        type=int,
        default=None,
        metavar="N",
        help="Maximum code-cell count before J012 is reported.",
    )
    parser.add_argument(
        "--notebook-check-jupyter-max-cell-lines",
        action="store",
        type=int,
        default=None,
        metavar="N",
        help="Maximum code-cell length before J012 is reported.",
    )
    parser.add_argument(
        "--notebook-check-jupyter-max-inline-definitions",
        action="store",
        type=int,
        default=None,
        metavar="N",
        help="Maximum inline definitions before J013 is reported.",
    )
    parser.add_argument(
        "--report-md",
        action="store",
        default=None,
        metavar="PATH",
        help="Write a markdown policy report to the provided path.",
    )
    parser.add_argument(
        "--report-dependency-enrichment",
        action="store_true",
        help="Add optional dependency metadata in the report.",
    )
    parser.add_argument(
        "--report-nbom-json",
        action="store",
        default=None,
        metavar="PATH",
        help="Write an NBOM-style JSON manifest for scanned notebooks.",
    )
    args = parser.parse_args()

    path_args = [str(Path(path).expanduser()) for path in args.paths]
    settings = _resolve_quality_settings(path_args, args)
    started_at = datetime.now(UTC)
    run_started_at = time.perf_counter()

    ruff_exit_code = 0
    if not args.skip_ruff:
        ruff_exit_code = _run_ruff(path_args)

    violations, scanned_files = _run_policy_checks(path_args, settings=settings)
    runtime_seconds = time.perf_counter() - run_started_at
    if settings.report_md is not None:
        _write_markdown_report(
            settings.report_md,
            settings=settings,
            violations=violations,
            scanned_files=scanned_files,
            started_at=started_at,
            runtime_seconds=runtime_seconds,
        )
    if settings.report_nbom_json is not None:
        analysis = _analyse_notebooks(scanned_files)
        dependencies = (
            _collect_dependency_metadata(analysis.imports)
            if settings.report_dependency_enrichment
            else []
        )
        _write_nbom_manifest(
            settings.report_nbom_json,
            settings=settings,
            violations=violations,
            scanned_files=scanned_files,
            analysis=analysis,
            dependency_rows=dependencies,
            started_at=started_at,
            runtime_seconds=runtime_seconds,
        )
    if violations:
        print("\npytest-notebook-policy violations")
        for violation in violations:
            print(f"{violation.path}:{violation.line}: {violation.code} {violation.message}")
        print(f"{len(violations)} violation(s) found.")

    if ruff_exit_code != 0 or violations:
        raise SystemExit(1)


def _run_ruff(paths: list[str]) -> int:
    command = [sys.executable, "-m", "ruff", "check", *paths]
    completed = subprocess.run(command, check=False)
    return completed.returncode


def _run_policy_checks(paths: list[str], settings: QualitySettings) -> tuple[list[Violation], list[Path]]:
    violations: list[Violation] = []
    scanned_files = list(_iter_notebook_files(paths))
    for path in scanned_files:
        violations.extend(
            scan_file(
                path,
                select=settings.select,
                ignore=settings.ignore,
                jupyter_source=settings.jupyter_source,
                max_code_cells=settings.max_code_cells,
                max_cell_lines=settings.max_cell_lines,
                max_inline_definitions=settings.max_inline_definitions,
            )
        )
    return sorted(violations, key=lambda v: (str(v.path), v.line, v.code)), scanned_files


def _iter_notebook_files(paths: list[str]):
    for raw in paths:
        path = Path(raw)
        if not path.exists():
            continue
        if path.is_file():
            if path.suffix in {".py", ".ipynb"}:
                yield path.resolve()
            continue
        for candidate in path.rglob("*"):
            if candidate.suffix not in {".py", ".ipynb"}:
                continue
            if any(part in EXCLUDED_DIRS for part in candidate.parts):
                continue
            yield candidate.resolve()


def _resolve_quality_settings(paths: list[str], args: argparse.Namespace) -> QualitySettings:
    defaults = _load_project_quality_defaults(paths)
    select = _normalise_rules(defaults.select_tokens)
    select.update(_normalise_rules(args.notebook_check_select))
    if not select:
        select = set(DEFAULT_RULES)

    ignore = _normalise_rules(defaults.ignore_tokens)
    ignore.update(_normalise_rules(args.notebook_check_ignore))

    jupyter_source = args.notebook_check_jupyter_source or defaults.jupyter_source or "ipynb"
    if jupyter_source not in JUPYTER_SOURCE_CHOICES:
        jupyter_source = "ipynb"

    max_code_cells = _coerce_positive_int(
        args.notebook_check_jupyter_max_code_cells
        if args.notebook_check_jupyter_max_code_cells is not None
        else defaults.max_code_cells,
        fallback=JUPYTER_MAX_CODE_CELLS,
    )
    max_cell_lines = _coerce_positive_int(
        args.notebook_check_jupyter_max_cell_lines
        if args.notebook_check_jupyter_max_cell_lines is not None
        else defaults.max_cell_lines,
        fallback=JUPYTER_MAX_CELL_LINES,
    )
    max_inline_definitions = _coerce_positive_int(
        args.notebook_check_jupyter_max_inline_definitions
        if args.notebook_check_jupyter_max_inline_definitions is not None
        else defaults.max_inline_definitions,
        fallback=JUPYTER_MAX_INLINE_DEFINITIONS,
    )
    report_md_raw = args.report_md if args.report_md is not None else defaults.report_md
    report_md = Path(report_md_raw).expanduser().resolve() if report_md_raw else None
    report_nbom_raw = (
        args.report_nbom_json if args.report_nbom_json is not None else defaults.report_nbom_json
    )
    report_nbom_json = (
        Path(report_nbom_raw).expanduser().resolve() if report_nbom_raw else None
    )
    report_dependency_enrichment = args.report_dependency_enrichment or bool(
        defaults.report_dependency_enrichment
    )

    return QualitySettings(
        select=select,
        ignore=ignore,
        jupyter_source=jupyter_source,
        max_code_cells=max_code_cells,
        max_cell_lines=max_cell_lines,
        max_inline_definitions=max_inline_definitions,
        report_md=report_md,
        report_dependency_enrichment=report_dependency_enrichment,
        report_nbom_json=report_nbom_json,
    )


def _load_project_quality_defaults(paths: list[str]) -> QualityDefaults:
    pyproject_path = _discover_pyproject_path(paths)
    if pyproject_path is None:
        return QualityDefaults()
    try:
        raw = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return QualityDefaults()

    tool = raw.get("tool", {})
    pytest_ini = tool.get("pytest", {}).get("ini_options", {})
    quality_tool = tool.get("pytest_notebook_policy", {}).get("quality", {})

    select_tokens = _coerce_tokens(pytest_ini.get("notebook_check_select"))
    select_tokens.extend(_coerce_tokens(quality_tool.get("select")))
    ignore_tokens = _coerce_tokens(pytest_ini.get("notebook_check_ignore"))
    ignore_tokens.extend(_coerce_tokens(quality_tool.get("ignore")))
    jupyter_source = _coerce_string(quality_tool.get("jupyter_source")) or _coerce_string(
        pytest_ini.get("notebook_check_jupyter_source")
    )
    max_code_cells = _coerce_positive_int(
        quality_tool.get("jupyter_max_code_cells", pytest_ini.get("notebook_check_jupyter_max_code_cells")),
        fallback=None,
    )
    max_cell_lines = _coerce_positive_int(
        quality_tool.get("jupyter_max_cell_lines", pytest_ini.get("notebook_check_jupyter_max_cell_lines")),
        fallback=None,
    )
    max_inline_definitions = _coerce_positive_int(
        quality_tool.get(
            "jupyter_max_inline_definitions", pytest_ini.get("notebook_check_jupyter_max_inline_definitions")
        ),
        fallback=None,
    )
    report_md = _coerce_string(quality_tool.get("report_md"))
    report_dependency_enrichment = _coerce_bool(quality_tool.get("report_dependency_enrichment"))
    report_nbom_json = _coerce_string(quality_tool.get("report_nbom_json"))
    return QualityDefaults(
        select_tokens=tuple(select_tokens),
        ignore_tokens=tuple(ignore_tokens),
        jupyter_source=jupyter_source,
        max_code_cells=max_code_cells,
        max_cell_lines=max_cell_lines,
        max_inline_definitions=max_inline_definitions,
        report_md=report_md,
        report_dependency_enrichment=report_dependency_enrichment,
        report_nbom_json=report_nbom_json,
    )


def _discover_pyproject_path(paths: list[str]) -> Path | None:
    cwd_candidate = Path.cwd() / "pyproject.toml"
    if cwd_candidate.exists():
        return cwd_candidate
    for raw in paths:
        candidate = Path(raw).expanduser().resolve()
        search_root = candidate.parent if candidate.is_file() else candidate
        for parent in [search_root, *search_root.parents]:
            project_file = parent / "pyproject.toml"
            if project_file.exists():
                return project_file
    return None


def _normalise_rules(values: tuple[str, ...] | list[str]) -> set[str]:
    normalised: set[str] = set()
    for raw in values:
        for part in str(raw).split(","):
            token = part.strip().upper()
            if token:
                normalised.add(token)
    return normalised


def _coerce_tokens(raw: object) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, str)]
    return []


def _coerce_string(raw: object) -> str | None:
    if not isinstance(raw, str):
        return None
    value = raw.strip()
    return value or None


def _coerce_bool(raw: object) -> bool | None:
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        lowered = raw.strip().lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off"}:
            return False
    return None


def _coerce_positive_int(raw: object, fallback: int | None) -> int | None:
    if raw is None:
        return fallback
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return fallback
    if value <= 0:
        return fallback
    return value


def _write_markdown_report(
    destination: Path,
    settings: QualitySettings,
    violations: list[Violation],
    scanned_files: list[Path],
    started_at: datetime,
    runtime_seconds: float,
) -> None:
    analysis = _analyse_notebooks(scanned_files)
    dependencies = _collect_dependency_metadata(analysis.imports) if settings.report_dependency_enrichment else []

    lines: list[str] = []
    status = "✅ Pass" if not violations else "⚠️ Findings"
    lines.append("## 🧪 Notebook policy report")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Status | {status} |")
    lines.append(f"| Generated | `{started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}` |")
    lines.append(f"| Runtime | `{runtime_seconds:.2f}s` |")
    lines.append(f"| Files scanned | `{len(scanned_files)}` |")
    lines.append(f"| Violations | `{len(violations)}` |")
    lines.append("")
    lines.append("### 🔎 Findings")
    lines.append("")
    if not violations:
        lines.append("No notebook policy violations were found.")
    else:
        lines.append("| File | Rule | Line | What | Why this is undesirable | Suggested fix |")
        lines.append("|---|---|---:|---|---|---|")
        for violation in violations:
            why, remediation = RULE_GUIDANCE.get(
                violation.code,
                (
                    "This rule highlights a notebook policy concern.",
                    "Review the rule context and apply an appropriate fix.",
                ),
            )
            lines.append(
                f"| `{_display_path(violation.path)}` | {_rule_link(violation.code)} | `{violation.line}` | "
                f"{_escape_markdown_table_text(violation.message)} | {_escape_markdown_table_text(why)} | "
                f"{_escape_markdown_table_text(remediation)} |"
            )
    lines.append("")
    lines.append("### 🧭 Notebook surface summary")
    lines.append("")
    lines.append("| Category | Count |")
    lines.append("|---|---:|")
    lines.append(f"| Key imports | `{len(analysis.imports)}` |")
    lines.append(f"| File references | `{len(analysis.file_references)}` |")
    lines.append(f"| HTTP requests | `{len(analysis.http_requests)}` |")
    lines.append(f"| Data sources | `{len(analysis.data_sources)}` |")
    lines.append("")
    lines.append("#### Key imports")
    lines.append("")
    lines.append("| Import |")
    lines.append("|---|")
    for name in sorted(analysis.imports):
        lines.append(f"| `{name}` |")
    if not analysis.imports:
        lines.append("| `(none)` |")
    lines.append("")
    lines.extend(_observed_table("#### File references", "Reference", analysis.file_references))
    lines.extend(_observed_table("#### HTTP requests", "Endpoint", analysis.http_requests))
    lines.extend(_observed_table("#### Data sources", "Source", analysis.data_sources))

    lines.append("## Appendix A — Configuration")
    lines.append("")
    lines.append("| Setting | Value |")
    lines.append("|---|---|")
    lines.append(f"| Enabled rules/prefixes | `{', '.join(sorted(settings.select)) or '(none)'}` |")
    lines.append(f"| Ignored rules/prefixes | `{', '.join(sorted(settings.ignore)) or '(none)'}` |")
    lines.append(f"| Jupyter source mode | `{settings.jupyter_source}` |")
    lines.append(f"| Jupyter max code cells | `{settings.max_code_cells}` |")
    lines.append(f"| Jupyter max cell lines | `{settings.max_cell_lines}` |")
    lines.append(f"| Jupyter max inline definitions | `{settings.max_inline_definitions}` |")
    lines.append(f"| Dependency enrichment | `{settings.report_dependency_enrichment}` |")
    lines.append(f"| NBOM output path | `{settings.report_nbom_json or '(disabled)'}` |")
    lines.append("")
    lines.append("## Appendix B — Scanned files")
    lines.append("")
    lines.append("| File | Type |")
    lines.append("|---|---|")
    for scanned_path in scanned_files:
        lines.append(f"| `{_display_path(scanned_path)}` | `{scanned_path.suffix or 'n/a'}` |")
    if not scanned_files:
        lines.append("| `(none)` | `n/a` |")

    if settings.report_dependency_enrichment:
        lines.append("")
        lines.append("## Appendix C — Dependency enrichment")
        lines.append("")
        lines.append("| Import | Package | Version | Licence | Homepage |")
        lines.append("|---|---|---|---|---|")
        for record in dependencies:
            lines.append(
                f"| `{record[0]}` | `{record[1]}` | `{record[2]}` | "
                f"`{_escape_markdown_table_text(record[3])}` | `{_escape_markdown_table_text(record[4])}` |"
            )
        if not dependencies:
            lines.append("| `(none)` | `(none)` | `(none)` | `(none)` | `(none)` |")

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _observed_table(title: str, value_label: str, values: set[Observed]) -> list[str]:
    lines: list[str] = []
    lines.append(title)
    lines.append("")
    lines.append(f"| File | {value_label} |")
    lines.append("|---|---|")
    for observed in sorted(values, key=lambda item: (_display_path(item.path), item.value)):
        lines.append(f"| `{_display_path(observed.path)}` | `{_escape_markdown_table_text(observed.value)}` |")
    if not values:
        lines.append("| `(none)` | `(none)` |")
    lines.append("")
    return lines


def _analyse_notebooks(scanned_files: list[Path]) -> NotebookAnalysis:
    imports: set[str] = set()
    file_references: set[Observed] = set()
    http_requests: set[Observed] = set()
    data_sources: set[Observed] = set()
    for path in scanned_files:
        for source in _source_blocks(path):
            if not source.strip():
                continue
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue
            imports.update(_extract_imports(tree))
            for literal in _extract_literals(tree):
                if _looks_like_file_reference(literal):
                    file_references.add(Observed(path=path, value=literal))
                if _looks_like_http(literal):
                    http_requests.add(Observed(path=path, value=literal))
                if _looks_like_data_source(literal):
                    data_sources.add(Observed(path=path, value=literal))
    return NotebookAnalysis(
        imports=imports,
        file_references=file_references,
        http_requests=http_requests,
        data_sources=data_sources,
    )


def _source_blocks(path: Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    if path.suffix != ".ipynb":
        return [content]
    try:
        notebook = json.loads(content)
    except json.JSONDecodeError:
        return []
    cells = notebook.get("cells")
    if not isinstance(cells, list):
        return []
    extracted: list[str] = []
    for cell in cells:
        if not isinstance(cell, dict) or cell.get("cell_type") != "code":
            continue
        source = cell.get("source")
        if isinstance(source, str):
            extracted.append(source)
        elif isinstance(source, list):
            extracted.append("".join(part for part in source if isinstance(part, str)))
    return extracted


def _extract_imports(tree: ast.AST) -> set[str]:
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", maxsplit=1)[0])
    return imports


def _extract_literals(tree: ast.AST) -> set[str]:
    literals: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value.strip()
            if value:
                literals.add(value)
    return literals


def _looks_like_file_reference(value: str) -> bool:
    if _looks_like_http(value) or _looks_like_data_source(value):
        return False
    if value.endswith(FILE_HINT_SUFFIXES):
        return True
    return "/" in value or value.startswith("./") or value.startswith("../")


def _looks_like_http(value: str) -> bool:
    return bool(HTTP_PATTERN.match(value))


def _looks_like_data_source(value: str) -> bool:
    return value.lower().startswith(DATA_SOURCE_PREFIXES)


def _collect_dependency_metadata(import_names: set[str]) -> list[tuple[str, str, str, str, str]]:
    mapping = importlib_metadata.packages_distributions()
    rows: list[tuple[str, str, str, str, str]] = []
    for import_name in sorted(import_names):
        distributions = sorted(mapping.get(import_name, []))
        if not distributions:
            rows.append((import_name, "(unresolved)", "-", "-", "-"))
            continue
        distribution = distributions[0]
        try:
            metadata = importlib_metadata.metadata(distribution)
            version = importlib_metadata.version(distribution)
        except importlib_metadata.PackageNotFoundError:
            rows.append((import_name, distribution, "-", "-", "-"))
            continue
        package_name = metadata.get("Name", distribution)
        license_name = metadata.get("License", "-") or "-"
        homepage = metadata.get("Home-page", "-") or "-"
        rows.append((import_name, package_name, version, license_name, homepage))
    return rows


def _write_nbom_manifest(
    destination: Path,
    settings: QualitySettings,
    violations: list[Violation],
    scanned_files: list[Path],
    analysis: NotebookAnalysis,
    dependency_rows: list[tuple[str, str, str, str, str]],
    started_at: datetime,
    runtime_seconds: float,
) -> None:
    dependency_capability_map = _dependency_capabilities(dependency_rows)
    manifest = {
        "schema_version": "0.1",
        "generated_at": started_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "runtime_seconds": round(runtime_seconds, 4),
        "tool": "pytest-notebook-policy",
        "settings": {
            "select": sorted(settings.select),
            "ignore": sorted(settings.ignore),
            "jupyter_source": settings.jupyter_source,
            "max_code_cells": settings.max_code_cells,
            "max_cell_lines": settings.max_cell_lines,
            "max_inline_definitions": settings.max_inline_definitions,
            "dependency_enrichment": settings.report_dependency_enrichment,
        },
        "files": [
            {"path": _display_path(path), "type": path.suffix or "n/a"}
            for path in scanned_files
        ],
        "violations": [
            {
                "path": _display_path(violation.path),
                "line": violation.line,
                "code": violation.code,
                "message": violation.message,
            }
            for violation in violations
        ],
        "surface": {
            "imports": sorted(analysis.imports),
            "file_references": [
                {"path": _display_path(item.path), "value": item.value}
                for item in sorted(
                    analysis.file_references,
                    key=lambda item: (_display_path(item.path), item.value),
                )
            ],
            "http_requests": [
                {"path": _display_path(item.path), "value": item.value}
                for item in sorted(
                    analysis.http_requests,
                    key=lambda item: (_display_path(item.path), item.value),
                )
            ],
            "data_sources": [
                {"path": _display_path(item.path), "value": item.value}
                for item in sorted(
                    analysis.data_sources,
                    key=lambda item: (_display_path(item.path), item.value),
                )
            ],
        },
        "dependencies": [
            {
                "import": row[0],
                "package": row[1],
                "version": row[2],
                "licence": row[3],
                "homepage": row[4],
                "capabilities": sorted(dependency_capability_map.get(row[0], set())),
            }
            for row in dependency_rows
        ],
        "summary": {
            "files_scanned": len(scanned_files),
            "violations": len(violations),
            "imports": len(analysis.imports),
            "file_references": len(analysis.file_references),
            "http_requests": len(analysis.http_requests),
            "data_sources": len(analysis.data_sources),
            "dependencies": len(dependency_rows),
        },
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _dependency_capabilities(
    dependency_rows: list[tuple[str, str, str, str, str]]
) -> dict[str, set[str]]:
    capabilities: dict[str, set[str]] = {}
    for import_name, package_name, *_ in dependency_rows:
        key = import_name.lower()
        inferred: set[str] = set()
        if key in {"requests", "httpx", "urllib3"}:
            inferred.add("http_requests")
        if key in {"pandas", "pyarrow", "openpyxl"}:
            inferred.update({"file_references", "data_sources"})
        if key in {"sqlalchemy", "psycopg2", "mysql", "sqlite3"}:
            inferred.add("data_sources")
        if package_name == "(unresolved)":
            inferred.add("unresolved")
        capabilities[import_name] = inferred
    return capabilities


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def _rule_link(code: str) -> str:
    return f"[`{code}`]({RULES_DOC_URL_BASE}#{code.lower()})"


def _escape_markdown_table_text(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()