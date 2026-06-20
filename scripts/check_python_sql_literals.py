from __future__ import annotations

import argparse
import ast
from pathlib import Path
import re


ALLOW_MARKER = "allow-sql-literal"
PRIMARY_SQL_KEYWORDS = (
    re.compile(r"\bselect\b[\s\S]{0,300}\bfrom\b", flags=re.IGNORECASE),
    re.compile(r"\binsert\b[\s\S]{0,200}\binto\b", flags=re.IGNORECASE),
    re.compile(r"\bupdate\b[\s\S]{0,200}\bset\b", flags=re.IGNORECASE),
    re.compile(r"\bdelete\b[\s\S]{0,200}\bfrom\b", flags=re.IGNORECASE),
    re.compile(r"\bcreate\b[\s\S]{0,200}\btable\b", flags=re.IGNORECASE),
    re.compile(r"\bdrop\b[\s\S]{0,200}\btable\b", flags=re.IGNORECASE),
    re.compile(r"\balter\b[\s\S]{0,200}\btable\b", flags=re.IGNORECASE),
    re.compile(r"\bwith\b[\s\S]{0,240}\bselect\b", flags=re.IGNORECASE),
)
MULTISPACE_PATTERN = re.compile(r"\s+")


def _normalise_text(text: str) -> str:
    return MULTISPACE_PATTERN.sub(" ", text).strip()


def _contains_sql_shape(text: str) -> bool:
    if len(text) < 25:
        return False
    normalised = _normalise_text(text)
    return any(pattern.search(normalised) for pattern in PRIMARY_SQL_KEYWORDS)


def _string_from_node(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value

    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            else:
                parts.append("{expr}")
        return "".join(parts)

    return None


def _line_has_allow_marker(lines: list[str], line_number: int) -> bool:
    zero_based = line_number - 1
    candidate_lines: list[str] = []
    if 0 <= zero_based < len(lines):
        candidate_lines.append(lines[zero_based])
    if 0 <= zero_based - 1 < len(lines):
        candidate_lines.append(lines[zero_based - 1])
    return any(ALLOW_MARKER in line for line in candidate_lines)


def _check_python_file(path: Path) -> list[str]:
    errors: list[str] = []
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return errors

    for node in ast.walk(tree):
        text = _string_from_node(node)
        if text is None:
            continue
        if not _contains_sql_shape(text):
            continue

        line_number = getattr(node, "lineno", 1)
        if _line_has_allow_marker(lines, line_number):
            continue

        snippet = _normalise_text(text)[:120]
        errors.append(
            (
                f"{path}:{line_number}: likely embedded SQL literal detected; "
                f"move to query builder/constant module or annotate with {ALLOW_MARKER}. "
                f"Snippet: {snippet!r}"
            )
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Flag likely SQL embedded directly in Python string literals. "
            "Use allow-sql-literal marker only when intentional."
        )
    )
    parser.add_argument("files", nargs="*", help="Python files to scan.")
    args = parser.parse_args()

    all_errors: list[str] = []
    for file_path in args.files:
        path = Path(file_path)
        if not path.exists() or path.is_dir() or path.suffix != ".py":
            continue
        all_errors.extend(_check_python_file(path))

    if all_errors:
        for error in all_errors:
            print(error)
        print(
            "Hint: add '# allow-sql-literal' on the same or preceding line for intentional SQL literals."
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
