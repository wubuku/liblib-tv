#!/usr/bin/env python3
"""Batch 858 helper: check whether Tailwind utility classes actually exist in
the **built CSS** (dev 4317 bundle and/or the `next build` output).

Why this exists
---------------
4317's Tailwind scan is *frozen* (batch 824): a utility class only has a rule
if some file that was scanned already used it.  Writing a source-only class
name therefore produces **silently unstyled** DOM -- no error, no red gate,
just the wrong pixels.

The class name in the emitted CSS is escaped by Tailwind, e.g. the utility
`text-white/88` becomes the selector `.text-white\\/88`.  A naive substring
search for the raw class name therefore reports 0 hits for a class that IS
present.  This helper escapes the class the same way Tailwind does and then
searches, so a "0 hits" answer means "not in the CSS" and not "my grep was
wrong".

Usage:
    python3 scripts/check-tailwind-classes-in-css.py <css-file> [<css-file> ...]
    python3 scripts/check-tailwind-classes-in-css.py --list-from <file>

`<file>` for --list-from holds one class per line; blank lines and `#`
comments are ignored.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Tailwind escapes these characters inside a class selector.
_ESCAPE_RE = re.compile(r"([\[\]\(\)\.,:/#%!])")


def escape_class(name: str) -> str:
    """Escape a utility class the way Tailwind's CSS selector does.

    Tailwind writes `.text-white\\/88` for `text-white/88`, i.e. the slash
    becomes a backslash-slash pair in the file.  In a Python string that is
    the two characters `\\` + `/`, which is what the replacement below
    produces.
    """
    return _ESCAPE_RE.sub(lambda m: "\\" + m.group(1), name)


def css_files(explicit: list[str]) -> list[Path]:
    out: list[Path] = []
    for arg in explicit:
        p = Path(arg)
        if p.is_file():
            out.append(p)
        elif p.is_dir():
            out.extend(sorted(p.rglob("*.css")))
    if out:
        return out
    # default: dev bundle + prod bundle
    dev = list((REPO / ".next/dev/static/chunks").glob("*.css"))
    prod = list((REPO / ".next/static/chunks").glob("*.css"))
    return dev + prod


def main(argv: list[str]) -> int:
    args = argv[1:]
    classes: list[str] = []
    files: list[str] = []
    i = 0
    while i < len(args):
        if args[i] == "--list-from":
            i += 1
            for line in Path(args[i]).read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    classes.append(line)
        else:
            files.append(args[i])
        i += 1

    if not classes:
        print("no classes to check (use --list-from <file>)")
        return 2

    targets = css_files(files)
    if not targets:
        print("no CSS files found -- did you run `next build`?")
        return 2

    blobs = [(p, p.read_text(encoding="utf-8", errors="replace")) for p in targets]
    missing: list[str] = []
    for cls in classes:
        needle = "." + escape_class(cls)
        hits = [p.name for p, text in blobs if needle in text]
        if hits:
            print(f"OK   {cls}  <- {hits[0]}" + (f" (+{len(hits)-1} more)" if len(hits) > 1 else ""))
        else:
            missing.append(cls)
            print(f"MISS {cls}")

    if missing:
        print(f"\n{len(missing)} class(es) NOT present in any CSS bundle:")
        for cls in missing:
            print("  -", cls)
        return 1
    print(f"\nall {len(classes)} classes present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
