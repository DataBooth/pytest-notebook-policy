from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path

import pytest

DEFAULT_RULES = (
    "M001",
    "M002",
    "M003",
    "M004",
    "M005",
    "M006",
    "J001",
    "J002",
    "J011",
    "J012",
    "J013",
)
EXCLUDED_DIRS = {".git", ".hg", ".svn", ".venv", "venv", "__pycache__", ".pytest_cache"}
APP_NAMES = {"app"}
MUTATING_METHODS = {
    "append",
    "clear",
    "discard",
    "extend",
    "insert",
    "pop",
    "remove",
    "reverse",
    "setdefault",
    "sort",
    "update",
}
NON_IDEMPOTENT_CALLS = {
    "datetime.date.today",
    "datetime.datetime.now",
    "datetime.datetime.today",
    "datetime.datetime.utcnow",
    "random.betavariate",
    "random.choice",
    "random.choices",
    "random.expovariate",
    "random.gauss",
    "random.gammavariate",
    "random.lognormvariate",
    "random.randint",
    "random.random",
    "random.randrange",
    "random.sample",
    "random.shuffle",
    "random.triangular",
    "random.uniform",
    "secrets.choice",
    "secrets.randbelow",
    "secrets.randbits",
    "secrets.token_bytes",
    "secrets.token_hex",
    "secrets.token_urlsafe",
    "time.perf_counter",
    "time.time",
    "uuid.uuid4",
}
NON_IDEMPOTENT_PREFIXES = ("np.random.", "numpy.random.")
JUPYTER_PARAMETER_CELL_NAMES = {
    "config",
    "configuration",
    "param",
    "params",
    "parameter",
    "parameters",
    "settings",
}
JUPYTER_MAX_CODE_CELLS = 20
JUPYTER_MAX_CELL_LINES = 80
JUPYTER_MAX_INLINE_DEFINITIONS = 3
JUPYTER_ENVIRONMENT_LOOKAHEAD_CELLS = 5
JUPYTER_DATA_CONTRACT_LOOKAHEAD_CELLS = 5
JUPYTER_MAX_OUTPUT_BYTES_TOTAL = 200_000
JUPYTER_MAX_OUTPUT_BYTES_PER_CELL = 50_000
M021_MAX_INLINE_DEFINITIONS = 5
M021_MAX_INLINE_DEFINITION_LINES = 40
JUPYTER_SOURCE_CHOICES = ("ipynb", "paired-py")
JUPYTER_ENVIRONMENT_NAME_HINTS = {
    "python",
    "python_version",
    "runtime",
    "runtime_version",
    "dependencies",
    "dependency_versions",
    "requirements",
    "packages",
    "package_versions",
}
JUPYTER_ENVIRONMENT_TEXT_HINTS = (
    "python",
    "runtime",
    "requirements",
    "dependencies",
    "packages",
    "assumptions",
)
JUPYTER_DATA_INPUT_NAME_HINTS = {
    "data_path",
    "input_path",
    "dataset",
    "dataset_path",
    "source_uri",
    "input_uri",
    "inputs",
    "table_name",
}
JUPYTER_DATA_SCHEMA_NAME_HINTS = {
    "schema",
    "dtypes",
    "columns",
    "expected_columns",
    "shape",
    "expected_shape",
}
JUPYTER_DATA_CONTRACT_TEXT_HINTS = (
    "schema",
    "columns",
    "dtype",
    "shape",
    ".csv",
    ".parquet",
    ".json",
    "s3://",
    "gs://",
    "table",
    "dataset",
)
SIDE_EFFECT_BOUNDARY_PATTERN = re.compile(r"side[\\s\\-_]?effects?", re.IGNORECASE)
SIDE_EFFECT_CALL_NAMES = {
    "requests.post",
    "requests.put",
    "requests.patch",
    "requests.delete",
    "httpx.post",
    "httpx.put",
    "httpx.patch",
    "httpx.delete",
    "subprocess.run",
    "subprocess.call",
    "subprocess.check_call",
    "subprocess.check_output",
    "subprocess.Popen",
    "os.remove",
    "os.rename",
    "os.replace",
    "shutil.move",
    "shutil.copy",
    "shutil.copy2",
    "shutil.rmtree",
}
SIDE_EFFECT_METHOD_NAMES = {
    "write_text",
    "write_bytes",
    "mkdir",
    "unlink",
    "rename",
    "replace",
    "touch",
    "to_csv",
    "to_parquet",
    "to_json",
    "to_excel",
    "to_sql",
    "to_pickle",
    "savefig",
}
SECRET_NAME_HINTS = (
    "password",
    "passwd",
    "pwd",
    "token",
    "api_key",
    "apikey",
    "secret",
    "client_secret",
    "private_key",
    "access_key",
)
SECRET_PLACEHOLDER_HINTS = (
    "your_",
    "change_me",
    "placeholder",
    "example",
    "dummy",
    "xxxx",
    "<",
    ">",
)
SECRET_VALUE_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}", re.IGNORECASE),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z\\-_]{20,}"),
)
_VIOLATIONS_KEY: pytest.StashKey[list["Violation"]] = pytest.StashKey()


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    code: str
    message: str

    def format(self, root: Path) -> str:
        relative = self.path.relative_to(root) if self.path.is_relative_to(root) else self.path
        return f"{relative}:{self.line}: {self.code} {self.message}"


@dataclass(frozen=True)
class NotebookCell:
    index: int
    line_start: int
    source: str


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("notebook_policy")
    group.addoption(
        "--notebook-check",
        action="store_true",
        default=False,
        help="Enable notebook policy checks.",
    )
    group.addoption(
        "--notebook-check-select",
        action="append",
        default=[],
        metavar="RULE",
        help="Rule code or prefix to enable (repeatable, e.g. M001, J002, J01).",
    )
    group.addoption(
        "--notebook-check-ignore",
        action="append",
        default=[],
        metavar="RULE",
        help="Rule code or prefix to ignore (repeatable, e.g. M004).",
    )
    group.addoption(
        "--notebook-check-jupyter-source",
        action="store",
        default=None,
        choices=JUPYTER_SOURCE_CHOICES,
        metavar="SOURCE",
        help="Source used for Jupyter rule checks: ipynb or paired-py.",
    )
    group.addoption(
        "--notebook-check-jupyter-max-code-cells",
        action="store",
        type=int,
        default=None,
        metavar="N",
        help="Maximum code-cell count before J012 is reported.",
    )
    group.addoption(
        "--notebook-check-jupyter-max-cell-lines",
        action="store",
        type=int,
        default=None,
        metavar="N",
        help="Maximum code-cell length (in lines) before J012 is reported.",
    )
    group.addoption(
        "--notebook-check-jupyter-max-inline-definitions",
        action="store",
        type=int,
        default=None,
        metavar="N",
        help="Maximum inline function/class definitions before J013 is reported.",
    )
    parser.addini("notebook_check", "Enable notebook policy checks.", type="bool", default=False)
    parser.addini(
        "notebook_check_select",
        "Rule code prefixes to enable for notebook policy checks.",
        type="linelist",
        default=[],
    )
    parser.addini(
        "notebook_check_ignore",
        "Rule code prefixes to ignore for notebook policy checks.",
        type="linelist",
        default=[],
    )
    parser.addini(
        "notebook_check_jupyter_source",
        "Source used for Jupyter rule checks: ipynb or paired-py.",
        default="ipynb",
    )
    parser.addini(
        "notebook_check_jupyter_max_code_cells",
        "Maximum code-cell count before J012 is reported.",
        default=str(JUPYTER_MAX_CODE_CELLS),
    )
    parser.addini(
        "notebook_check_jupyter_max_cell_lines",
        "Maximum code-cell length (in lines) before J012 is reported.",
        default=str(JUPYTER_MAX_CELL_LINES),
    )
    parser.addini(
        "notebook_check_jupyter_max_inline_definitions",
        "Maximum inline function/class definitions before J013 is reported.",
        default=str(JUPYTER_MAX_INLINE_DEFINITIONS),
    )


def pytest_sessionstart(session: pytest.Session) -> None:
    if not _is_enabled(session.config):
        return

    select = _resolve_select(session.config)
    ignore = _resolve_ignore(session.config)
    jupyter_source = _resolve_jupyter_source(session.config)
    max_code_cells = _resolve_jupyter_max_code_cells(session.config)
    max_cell_lines = _resolve_jupyter_max_cell_lines(session.config)
    max_inline_definitions = _resolve_jupyter_max_inline_definitions(session.config)
    violations: list[Violation] = []
    for candidate in _iter_candidate_files(session.config):
        violations.extend(
            scan_file(
                candidate,
                select=select,
                ignore=ignore,
                jupyter_source=jupyter_source,
                max_code_cells=max_code_cells,
                max_cell_lines=max_cell_lines,
                max_inline_definitions=max_inline_definitions,
            )
        )
    session.config.stash[_VIOLATIONS_KEY] = violations


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter,
    exitstatus: int,  # noqa: ARG001
    config: pytest.Config,
) -> None:
    violations = config.stash.get(_VIOLATIONS_KEY, [])
    if not violations:
        return

    terminalreporter.section("pytest-notebook-policy")
    for violation in violations:
        terminalreporter.line(violation.format(config.rootpath))
    terminalreporter.line(f"{len(violations)} notebook policy violation(s) found.")


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    violations = session.config.stash.get(_VIOLATIONS_KEY, [])
    if violations and exitstatus == pytest.ExitCode.OK:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


def scan_file(
    path: Path,
    select: set[str],
    ignore: set[str],
    jupyter_source: str = "ipynb",
    max_code_cells: int = JUPYTER_MAX_CODE_CELLS,
    max_cell_lines: int = JUPYTER_MAX_CELL_LINES,
    max_inline_definitions: int = JUPYTER_MAX_INLINE_DEFINITIONS,
) -> list[Violation]:
    if path.suffix == ".ipynb":
        return _scan_jupyter_file(
            path,
            select=select,
            ignore=ignore,
            jupyter_source=jupyter_source,
            max_code_cells=max_code_cells,
            max_cell_lines=max_cell_lines,
            max_inline_definitions=max_inline_definitions,
        )
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    if not is_marimo_notebook(tree):
        return []

    violations: list[Violation] = []
    if _rule_enabled("M001", select, ignore):
        violations.extend(_check_on_change(path, tree))
    if _rule_enabled("M002", select, ignore):
        violations.extend(_check_mixed_test_cells(path, tree))
    if _rule_enabled("M003", select, ignore):
        violations.extend(_check_module_assignments(path, tree))
    if _rule_enabled("M004", select, ignore):
        violations.extend(_check_fixture_in_notebook(path, tree))
    if _rule_enabled("M005", select, ignore):
        violations.extend(_check_cross_cell_mutation(path, tree))
    if _rule_enabled("M006", select, ignore):
        violations.extend(_check_non_idempotent_cells(path, tree))
    return violations


def _check_jupyter_parameter_cell(path: Path, cells: list[NotebookCell]) -> list[Violation]:
    candidate_cells = [cell for cell in cells if cell.source.strip()][:3]
    if not candidate_cells:
        return []

    if any(_looks_like_parameter_cell(cell.source) for cell in candidate_cells):
        return []

    first = candidate_cells[0]
    return [
        Violation(
            path=path,
            line=first.line_start,
            code="J011",
            message=(
                "Add a top-of-notebook parameter/configuration cell (within the first three code cells) "
                "to make runs reproducible and easier to automate."
            ),
        )
    ]


def _looks_like_parameter_cell(source: str) -> bool:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False

    has_assignment = False
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return False
        if isinstance(node, (ast.For, ast.AsyncFor, ast.While, ast.If, ast.With, ast.Try, ast.Match)):
            return False
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if not isinstance(target, ast.Name):
                    continue
                if target.id.lower() in JUPYTER_PARAMETER_CELL_NAMES:
                    has_assignment = True
                elif isinstance(getattr(node, "value", None), ast.Constant):
                    has_assignment = True
                elif isinstance(getattr(node, "value", None), (ast.List, ast.Tuple, ast.Dict, ast.Set)):
                    has_assignment = True
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        else:
            return False
    return has_assignment


def _check_jupyter_notebook_size(
    path: Path, cells: list[NotebookCell], max_code_cells: int, max_cell_lines: int
) -> list[Violation]:
    violations: list[Violation] = []

    if len(cells) > max_code_cells:
        violations.append(
            Violation(
                path=path,
                line=cells[0].line_start,
                code="J012",
                message=(
                    f"Notebook has {len(cells)} code cells; keep notebooks under {max_code_cells} "
                    "code cells or split into smaller notebooks/modules."
                ),
            )
        )

    for cell in cells:
        line_count = len(cell.source.splitlines())
        if line_count <= max_cell_lines:
            continue
        violations.append(
            Violation(
                path=path,
                line=cell.line_start,
                code="J012",
                message=(
                    f"Code cell is {line_count} lines long; keep cells under {max_cell_lines} lines "
                    "and move complex logic into modules."
                ),
            )
        )
    return violations


def _check_jupyter_inline_definitions(
    path: Path, cells: list[NotebookCell], max_inline_definitions: int
) -> list[Violation]:
    definition_count = 0
    first_definition_line: int | None = None

    for cell in cells:
        if not cell.source.strip():
            continue
        try:
            tree = ast.parse(cell.source, filename=f"{path}#cell{cell.index}")
        except SyntaxError:
            continue

        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            definition_count += 1
            if first_definition_line is None:
                first_definition_line = cell.line_start + node.lineno - 1

    if definition_count <= max_inline_definitions:
        return []

    return [
        Violation(
            path=path,
            line=first_definition_line or cells[0].line_start,
            code="J013",
            message=(
                f"Notebook defines {definition_count} functions/classes inline; keep at most "
                f"{max_inline_definitions} and extract reusable logic into importable modules."
            ),
        )
    ]


def _check_jupytext_sync(path: Path) -> list[Violation]:
    script_path = path.with_suffix(".py")
    if not script_path.exists():
        return [
            Violation(
                path=path,
                line=1,
                code="J010",
                message=(
                    "No paired .py notebook script found for sync checks; "
                    "create a paired file or disable J010."
                ),
            )
        ]

    try:
        import jupytext
    except ImportError:
        return [
            Violation(
                path=path,
                line=1,
                code="J010",
                message="Install optional sync dependencies: `uv add --dev 'pytest-notebook-policy[sync]'`.",
            )
        ]

    try:
        notebook_ipynb = jupytext.read(path)
        notebook_script = jupytext.read(script_path)
    except Exception as exc:  # noqa: BLE001
        return [
            Violation(
                path=path,
                line=1,
                code="J010",
                message=f"Unable to parse paired notebook/script for sync check: {exc}",
            )
        ]

    ipynb_cells = [cell.source.strip() for cell in notebook_ipynb.cells if cell.cell_type == "code"]
    script_cells = [cell.source.strip() for cell in notebook_script.cells if cell.cell_type == "code"]
    if ipynb_cells != script_cells:
        return [
            Violation(
                path=path,
                line=1,
                code="J010",
                message="Paired .ipynb and .py notebook sources are out of sync.",
            )
        ]
    return []


def _scan_jupyter_file(
    path: Path,
    select: set[str],
    ignore: set[str],
    jupyter_source: str,
    max_code_cells: int,
    max_cell_lines: int,
    max_inline_definitions: int,
) -> list[Violation]:
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    try:
        notebook = json.loads(source)
    except json.JSONDecodeError:
        return []

    ipynb_cells = _extract_notebook_cells(notebook)
    if not ipynb_cells:
        return []
    rule_cells = _select_jupyter_rule_cells(path, ipynb_cells=ipynb_cells, mode=jupyter_source)

    violations: list[Violation] = []
    if _rule_enabled("J001", select, ignore):
        violations.extend(_check_jupyter_magic_usage(path, rule_cells))
    if _rule_enabled("J002", select, ignore):
        violations.extend(_check_jupyter_non_idempotent_cells(path, rule_cells))
    if _rule_enabled("J011", select, ignore):
        violations.extend(_check_jupyter_parameter_cell(path, rule_cells))
    if _rule_enabled("J012", select, ignore):
        violations.extend(
            _check_jupyter_notebook_size(
                path,
                rule_cells,
                max_code_cells=max_code_cells,
                max_cell_lines=max_cell_lines,
            )
        )
    if _rule_enabled("J013", select, ignore):
        violations.extend(
            _check_jupyter_inline_definitions(
                path, rule_cells, max_inline_definitions=max_inline_definitions
            )
        )
    if _rule_enabled("J010", select, ignore):
        violations.extend(_check_jupytext_sync(path))
    return violations


def _select_jupyter_rule_cells(path: Path, ipynb_cells: list[NotebookCell], mode: str) -> list[NotebookCell]:
    if mode != "paired-py":
        return ipynb_cells
    paired_cells = _extract_paired_script_cells(path)
    if paired_cells:
        return paired_cells
    return ipynb_cells


def _extract_paired_script_cells(path: Path) -> list[NotebookCell] | None:
    script_path = path.with_suffix(".py")
    if not script_path.exists():
        return None

    try:
        import jupytext
    except ImportError:
        return None

    try:
        notebook_script = jupytext.read(script_path)
    except Exception:  # noqa: BLE001
        return None

    sources = [cell.source for cell in notebook_script.cells if cell.cell_type == "code"]
    if not sources:
        return []
    return _cells_from_sources(sources)


def _extract_notebook_cells(notebook: dict) -> list[NotebookCell]:
    raw_cells = notebook.get("cells")
    if not isinstance(raw_cells, list):
        return []
    sources: list[str] = []
    for raw_cell in raw_cells:
        if not isinstance(raw_cell, dict):
            continue
        if raw_cell.get("cell_type") != "code":
            continue
        sources.append(_normalise_cell_source(raw_cell.get("source")))
    return _cells_from_sources(sources)


def _cells_from_sources(sources: list[str]) -> list[NotebookCell]:

    cells: list[NotebookCell] = []
    line_cursor = 1
    for index, source in enumerate(sources):
        cells.append(NotebookCell(index=index, line_start=line_cursor, source=source))
        line_cursor += source.count("\n") + 2
    return cells


def _normalise_cell_source(source: object) -> str:
    if isinstance(source, str):
        return source
    if isinstance(source, list):
        return "".join(part for part in source if isinstance(part, str))
    return ""


def _check_jupyter_magic_usage(path: Path, cells: list[NotebookCell]) -> list[Violation]:
    violations: list[Violation] = []
    for cell in cells:
        for offset, line in enumerate(cell.source.splitlines()):
            stripped = line.lstrip()
            if stripped.startswith("%") or stripped.startswith("!"):
                violations.append(
                    Violation(
                        path=path,
                        line=cell.line_start + offset,
                        code="J001",
                        message=(
                            "Avoid notebook magics/shell escapes in policy-checked notebooks; "
                            "prefer Python code for reliable .ipynb↔.py sync."
                        ),
                    )
                )
    return violations


def _check_jupyter_non_idempotent_cells(path: Path, cells: list[NotebookCell]) -> list[Violation]:
    violations: list[Violation] = []
    seen: set[tuple[int, str]] = set()

    for cell in cells:
        if not cell.source.strip():
            continue
        try:
            tree = ast.parse(cell.source, filename=f"{path}#cell{cell.index}")
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            call_name = _dotted_name(node.func)
            if call_name is None or not _is_non_idempotent_call(call_name):
                continue

            line = cell.line_start + node.lineno - 1
            key = (line, call_name)
            if key in seen:
                continue
            seen.add(key)
            violations.append(
                Violation(
                    path=path,
                    line=line,
                    code="J002",
                    message=(
                        f"`{call_name}()` can make notebook behaviour non-idempotent; "
                        "gate it behind explicit inputs or controlled seeds."
                    ),
                )
            )

    return violations


def is_marimo_notebook(tree: ast.AST) -> bool:
    imports_marimo = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == "marimo" for alias in node.names):
                imports_marimo = True
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("marimo"):
                imports_marimo = True

    has_cell = any(
        _is_cell_function(node)
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )
    return imports_marimo and has_cell


def _is_cell_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(_is_cell_decorator(decorator) for decorator in node.decorator_list)


def _is_cell_decorator(decorator: ast.expr) -> bool:
    if isinstance(decorator, ast.Attribute):
        return decorator.attr == "cell"
    if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
        return decorator.func.attr == "cell"
    return False


def _iter_cell_functions(tree: ast.AST) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_cell_function(node)
    ]


def _check_on_change(path: Path, tree: ast.AST) -> list[Violation]:
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg == "on_change":
                violations.append(
                    Violation(
                        path=path,
                        line=node.lineno,
                        code="M001",
                        message="Prefer reactive dependencies over on_change handlers.",
                    )
                )
    return violations


def _check_mixed_test_cells(path: Path, tree: ast.AST) -> list[Violation]:
    violations: list[Violation] = []
    for node in _iter_cell_functions(tree):
        has_test = False
        has_other = False
        for statement in node.body:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if statement.name.startswith("test_"):
                    has_test = True
                else:
                    has_other = True
                continue
            if _is_ignorable_in_test_cell(statement):
                continue
            has_other = True

        if has_test and has_other:
            violations.append(
                Violation(
                    path=path,
                    line=node.lineno,
                    code="M002",
                    message="Keep test cells focused: avoid mixing tests with setup/helper code.",
                )
            )
    return violations


def _is_ignorable_in_test_cell(statement: ast.stmt) -> bool:
    if isinstance(statement, (ast.Return, ast.Pass)):
        return True
    if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant):
        return isinstance(statement.value.value, str)
    return False


def _check_module_assignments(path: Path, tree: ast.Module) -> list[Violation]:
    violations: list[Violation] = []
    for statement in tree.body:
        names = _assignment_names(statement)
        if not names:
            continue
        for name, line in names:
            if _allowed_module_name(name):
                continue
            violations.append(
                Violation(
                    path=path,
                    line=line,
                    code="M003",
                    message="Avoid mutable module-level state; keep state inside cells/functions.",
                )
            )
    return violations


def _assignment_names(statement: ast.stmt) -> list[tuple[str, int]]:
    names: list[tuple[str, int]] = []
    if isinstance(statement, ast.Assign):
        for target in statement.targets:
            names.extend((name, statement.lineno) for name in _target_names(target))
    elif isinstance(statement, ast.AnnAssign):
        names.extend((name, statement.lineno) for name in _target_names(statement.target))
    elif isinstance(statement, ast.AugAssign):
        names.extend((name, statement.lineno) for name in _target_names(statement.target))
    return names


def _target_names(target: ast.expr) -> list[str]:
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, (ast.Tuple, ast.List)):
        names: list[str] = []
        for elt in target.elts:
            names.extend(_target_names(elt))
        return names
    return []


def _allowed_module_name(name: str) -> bool:
    if name in APP_NAMES:
        return True
    if name.startswith("__"):
        return True
    if name.isupper():
        return True
    return False


def _check_fixture_in_notebook(path: Path, tree: ast.AST) -> list[Violation]:
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if any(_is_fixture_decorator(decorator) for decorator in node.decorator_list):
            violations.append(
                Violation(
                    path=path,
                    line=node.lineno,
                    code="M004",
                    message="Prefer fixtures in conftest.py or helper modules for static collection.",
                )
            )
    return violations


def _is_fixture_decorator(decorator: ast.expr) -> bool:
    if isinstance(decorator, ast.Name):
        return decorator.id == "fixture"
    if isinstance(decorator, ast.Attribute):
        return isinstance(decorator.value, ast.Name) and decorator.value.id == "pytest" and decorator.attr == "fixture"
    if isinstance(decorator, ast.Call):
        return _is_fixture_decorator(decorator.func)
    return False


def _check_cross_cell_mutation(path: Path, tree: ast.Module) -> list[Violation]:
    violations: list[Violation] = []
    seen: set[tuple[int, str]] = set()
    module_mutables = _mutable_module_names(tree)

    for cell in _iter_cell_functions(tree):
        tracked_names = module_mutables | set(_cell_parameters(cell))

        for node in ast.walk(cell):
            if not isinstance(node, ast.Global):
                continue
            for name in node.names:
                key = (node.lineno, f"global:{name}")
                if key in seen:
                    continue
                seen.add(key)
                violations.append(
                    Violation(
                        path=path,
                        line=node.lineno,
                        code="M005",
                        message=f"Avoid `global {name}` in cells; keep mutations local to the defining cell.",
                    )
                )

        for node in _iter_runtime_nodes(cell):
            if isinstance(node, ast.Call) and _is_mutating_method_call(node, tracked_names):
                key = (node.lineno, "method")
                if key in seen:
                    continue
                seen.add(key)
                violations.append(
                    Violation(
                        path=path,
                        line=node.lineno,
                        code="M005",
                        message="Avoid cross-cell mutation of shared objects; prefer creating a new value.",
                    )
                )
                continue

            if _is_subscript_assignment_to_tracked_name(node, tracked_names):
                key = (node.lineno, "subscript")
                if key in seen:
                    continue
                seen.add(key)
                violations.append(
                    Violation(
                        path=path,
                        line=node.lineno,
                        code="M005",
                        message="Avoid mutating a shared container from another cell; derive a new object instead.",
                    )
                )

    return violations


def _mutable_module_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for statement in tree.body:
        if not isinstance(statement, ast.Assign):
            continue
        if not _looks_mutable_value(statement.value):
            continue
        for target in statement.targets:
            names.update(_target_names(target))
    return names


def _looks_mutable_value(value: ast.expr) -> bool:
    if isinstance(value, (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp)):
        return True
    if isinstance(value, ast.Call):
        name = _dotted_name(value.func)
        return name in {"dict", "list", "set", "collections.defaultdict"}
    return False


def _cell_parameters(cell: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    names = [arg.arg for arg in cell.args.args]
    names.extend(arg.arg for arg in cell.args.posonlyargs)
    names.extend(arg.arg for arg in cell.args.kwonlyargs)
    if cell.args.vararg:
        names.append(cell.args.vararg.arg)
    if cell.args.kwarg:
        names.append(cell.args.kwarg.arg)
    return names


def _iter_runtime_nodes(cell: ast.FunctionDef | ast.AsyncFunctionDef):
    for statement in cell.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        yield statement
        yield from _walk_descendants_excluding_nested_functions(statement)


def _walk_descendants_excluding_nested_functions(node: ast.AST):
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        yield child
        yield from _walk_descendants_excluding_nested_functions(child)


def _is_mutating_method_call(call: ast.Call, tracked_names: set[str]) -> bool:
    if not isinstance(call.func, ast.Attribute):
        return False
    if call.func.attr not in MUTATING_METHODS:
        return False
    if not isinstance(call.func.value, ast.Name):
        return False
    return call.func.value.id in tracked_names


def _is_subscript_assignment_to_tracked_name(node: ast.AST, tracked_names: set[str]) -> bool:
    if isinstance(node, ast.Assign):
        targets: list[ast.expr] = list(node.targets)
    elif isinstance(node, ast.AnnAssign):
        targets = [node.target]
    elif isinstance(node, ast.AugAssign):
        targets = [node.target]
    else:
        return False

    for target in targets:
        if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
            if target.value.id in tracked_names:
                return True
    return False


def _check_non_idempotent_cells(path: Path, tree: ast.AST) -> list[Violation]:
    violations: list[Violation] = []
    seen: set[tuple[int, str]] = set()

    for cell in _iter_cell_functions(tree):
        for node in _iter_runtime_nodes(cell):
            if not isinstance(node, ast.Call):
                continue
            call_name = _dotted_name(node.func)
            if call_name is None or not _is_non_idempotent_call(call_name):
                continue
            key = (node.lineno, call_name)
            if key in seen:
                continue
            seen.add(key)
            violations.append(
                Violation(
                    path=path,
                    line=node.lineno,
                    code="M006",
                    message=f"`{call_name}()` can make cell behaviour non-idempotent; gate it behind explicit inputs.",
                )
            )
    return violations


def _dotted_name(expr: ast.expr) -> str | None:
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        root = _dotted_name(expr.value)
        if root:
            return f"{root}.{expr.attr}"
        return expr.attr
    return None


def _is_non_idempotent_call(call_name: str) -> bool:
    if call_name in NON_IDEMPOTENT_CALLS:
        return True
    return any(call_name.startswith(prefix) for prefix in NON_IDEMPOTENT_PREFIXES)


def _is_enabled(config: pytest.Config) -> bool:
    return bool(config.getoption("notebook_check")) or bool(config.getini("notebook_check"))


def _resolve_select(config: pytest.Config) -> set[str]:
    selected = _normalise_rules(config.getini("notebook_check_select"))
    selected.update(_normalise_rules(config.getoption("notebook_check_select")))
    if selected:
        return selected
    return set(DEFAULT_RULES)


def _resolve_ignore(config: pytest.Config) -> set[str]:
    ignored = _normalise_rules(config.getini("notebook_check_ignore"))
    ignored.update(_normalise_rules(config.getoption("notebook_check_ignore")))
    return ignored


def _resolve_jupyter_source(config: pytest.Config) -> str:
    cli_value = config.getoption("notebook_check_jupyter_source")
    if cli_value in JUPYTER_SOURCE_CHOICES:
        return cli_value

    ini_value = str(config.getini("notebook_check_jupyter_source")).strip().lower()
    if ini_value in JUPYTER_SOURCE_CHOICES:
        return ini_value
    return "ipynb"


def _resolve_jupyter_max_code_cells(config: pytest.Config) -> int:
    return _resolve_positive_int_option(
        config,
        option_name="notebook_check_jupyter_max_code_cells",
        ini_name="notebook_check_jupyter_max_code_cells",
        default=JUPYTER_MAX_CODE_CELLS,
    )


def _resolve_jupyter_max_cell_lines(config: pytest.Config) -> int:
    return _resolve_positive_int_option(
        config,
        option_name="notebook_check_jupyter_max_cell_lines",
        ini_name="notebook_check_jupyter_max_cell_lines",
        default=JUPYTER_MAX_CELL_LINES,
    )


def _resolve_jupyter_max_inline_definitions(config: pytest.Config) -> int:
    return _resolve_positive_int_option(
        config,
        option_name="notebook_check_jupyter_max_inline_definitions",
        ini_name="notebook_check_jupyter_max_inline_definitions",
        default=JUPYTER_MAX_INLINE_DEFINITIONS,
    )


def _resolve_positive_int_option(
    config: pytest.Config, option_name: str, ini_name: str, default: int
) -> int:
    cli_value = config.getoption(option_name)
    if cli_value is not None:
        return _coerce_positive_int(cli_value, default=default)
    ini_value = config.getini(ini_name)
    return _coerce_positive_int(ini_value, default=default)


def _coerce_positive_int(raw_value: object, default: int) -> int:
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return default
    if value <= 0:
        return default
    return value


def _normalise_rules(values: list[str]) -> set[str]:
    normalised: set[str] = set()
    for raw in values:
        for part in raw.split(","):
            token = part.strip().upper()
            if token:
                normalised.add(token)
    return normalised


def _rule_enabled(code: str, select: set[str], ignore: set[str]) -> bool:
    if any(code.startswith(prefix) for prefix in ignore):
        return False
    return any(code.startswith(prefix) for prefix in select)


def _iter_candidate_files(config: pytest.Config) -> list[Path]:
    candidates: list[Path] = []
    roots = config.args or [str(config.rootpath)]

    for root in roots:
        base = Path(root.split("::", maxsplit=1)[0])
        if not base.is_absolute():
            base = config.rootpath / base
        if not base.exists():
            continue
        if base.is_file():
            if base.suffix in {".py", ".ipynb"}:
                candidates.append(base.resolve())
            continue
        for path in base.rglob("*"):
            if path.suffix not in {".py", ".ipynb"}:
                continue
            if any(part in EXCLUDED_DIRS for part in path.parts):
                continue
            candidates.append(path.resolve())
    return sorted(set(candidates))
