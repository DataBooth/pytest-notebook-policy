from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

import pytest

DEFAULT_RULES = ("M001", "M002", "M003", "M004", "M005", "M006")
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


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("marimo")
    group.addoption(
        "--marimo-check",
        action="store_true",
        default=False,
        help="Enable marimo notebook quality checks.",
    )
    group.addoption(
        "--marimo-check-select",
        action="append",
        default=[],
        metavar="RULE",
        help="Rule code or prefix to enable (repeatable, e.g. M001 or M00).",
    )
    group.addoption(
        "--marimo-check-ignore",
        action="append",
        default=[],
        metavar="RULE",
        help="Rule code or prefix to ignore (repeatable, e.g. M004).",
    )
    parser.addini("marimo_check", "Enable pytest-marimo checks.", type="bool", default=False)
    parser.addini(
        "marimo_check_select",
        "Rule code prefixes to enable for marimo checks.",
        type="linelist",
        default=[],
    )
    parser.addini(
        "marimo_check_ignore",
        "Rule code prefixes to ignore for marimo checks.",
        type="linelist",
        default=[],
    )


def pytest_sessionstart(session: pytest.Session) -> None:
    if not _is_enabled(session.config):
        return

    select = _resolve_select(session.config)
    ignore = _resolve_ignore(session.config)
    violations: list[Violation] = []
    for candidate in _iter_candidate_files(session.config):
        violations.extend(scan_file(candidate, select=select, ignore=ignore))
    session.config.stash[_VIOLATIONS_KEY] = violations


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter,
    exitstatus: int,  # noqa: ARG001
    config: pytest.Config,
) -> None:
    violations = config.stash.get(_VIOLATIONS_KEY, [])
    if not violations:
        return

    terminalreporter.section("pytest-marimo")
    for violation in violations:
        terminalreporter.line(violation.format(config.rootpath))
    terminalreporter.line(f"{len(violations)} marimo violation(s) found.")


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    violations = session.config.stash.get(_VIOLATIONS_KEY, [])
    if violations and exitstatus == pytest.ExitCode.OK:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


def scan_file(path: Path, select: set[str], ignore: set[str]) -> list[Violation]:
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
    return bool(config.getoption("marimo_check")) or bool(config.getini("marimo_check"))


def _resolve_select(config: pytest.Config) -> set[str]:
    selected = _normalise_rules(config.getini("marimo_check_select"))
    selected.update(_normalise_rules(config.getoption("marimo_check_select")))
    if selected:
        return selected
    return set(DEFAULT_RULES)


def _resolve_ignore(config: pytest.Config) -> set[str]:
    ignored = _normalise_rules(config.getini("marimo_check_ignore"))
    ignored.update(_normalise_rules(config.getoption("marimo_check_ignore")))
    return ignored


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
            if base.suffix == ".py":
                candidates.append(base.resolve())
            continue
        for path in base.rglob("*.py"):
            if any(part in EXCLUDED_DIRS for part in path.parts):
                continue
            candidates.append(path.resolve())
    return sorted(set(candidates))
