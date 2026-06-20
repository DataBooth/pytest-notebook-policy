from __future__ import annotations

import argparse
from pathlib import Path


ALLOW_MARKER = "allow-text-safety"
INVISIBLE_OR_UNSAFE_CODEPOINTS = {
    "\u200b": "ZERO WIDTH SPACE",
    "\u200c": "ZERO WIDTH NON-JOINER",
    "\u200d": "ZERO WIDTH JOINER",
    "\u2060": "WORD JOINER",
    "\ufeff": "ZERO WIDTH NO-BREAK SPACE / BOM",
    "\u202a": "LEFT-TO-RIGHT EMBEDDING",
    "\u202b": "RIGHT-TO-LEFT EMBEDDING",
    "\u202c": "POP DIRECTIONAL FORMATTING",
    "\u202d": "LEFT-TO-RIGHT OVERRIDE",
    "\u202e": "RIGHT-TO-LEFT OVERRIDE",
    "\u2066": "LEFT-TO-RIGHT ISOLATE",
    "\u2067": "RIGHT-TO-LEFT ISOLATE",
    "\u2068": "FIRST STRONG ISOLATE",
    "\u2069": "POP DIRECTIONAL ISOLATE",
    "\ufffd": "REPLACEMENT CHARACTER",
}


def _looks_like_disallowed_control_character(character: str) -> bool:
    codepoint = ord(character)
    if codepoint in (9, 10, 13):
        return False
    if 0 <= codepoint <= 31:
        return True
    if codepoint == 127:
        return True
    return False


def _check_file(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return [f"{path}: unable to read file: {exc}"]

    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return [
            (
                f"{path}: invalid UTF-8 (byte offset {exc.start}-{exc.end}); "
                f"decode error: {exc.reason}"
            )
        ]

    for line_number, line in enumerate(content.splitlines(keepends=False), start=1):
        allow_marker_present = ALLOW_MARKER in line
        for column_number, character in enumerate(line, start=1):
            if character in INVISIBLE_OR_UNSAFE_CODEPOINTS:
                if allow_marker_present:
                    continue
                name = INVISIBLE_OR_UNSAFE_CODEPOINTS[character]
                codepoint = f"U+{ord(character):04X}"
                errors.append(
                    (
                        f"{path}:{line_number}:{column_number}: disallowed character "
                        f"{codepoint} ({name})"
                    )
                )
                continue

            if _looks_like_disallowed_control_character(character):
                if allow_marker_present:
                    continue
                codepoint = f"U+{ord(character):04X}"
                errors.append(
                    f"{path}:{line_number}:{column_number}: disallowed control character {codepoint}"
                )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate text safety for staged files: UTF-8 decode, suspicious invisible "
            "characters, and control characters."
        )
    )
    parser.add_argument("files", nargs="*", help="Files to validate.")
    args = parser.parse_args()

    all_errors: list[str] = []
    for file_path in args.files:
        path = Path(file_path)
        if not path.exists() or path.is_dir():
            continue
        all_errors.extend(_check_file(path))

    if all_errors:
        for error in all_errors:
            print(error)
        print(
            f"Hint: add '{ALLOW_MARKER}' on the specific line only when the character is intentional."
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
