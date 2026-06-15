#!/usr/bin/env python3
"""Dump the PDF bookmark/outline tree (title + page) to stdout.

Tries pypdf/PyPDF2 if available; otherwise prints nothing and exits 0 so the
caller can fall back to manual TOC inspection.
"""
import sys


def main(path: str) -> int:
    try:
        try:
            from pypdf import PdfReader  # type: ignore
        except ImportError:
            from PyPDF2 import PdfReader  # type: ignore
    except ImportError:
        sys.stderr.write("pypdf/PyPDF2 not installed; skipping outline dump\n")
        return 0

    reader = PdfReader(path)

    def page_of(dest):
        try:
            return reader.get_destination_page_number(dest) + 1
        except Exception:
            return "?"

    def walk(items, depth=0):
        for it in items:
            if isinstance(it, list):
                walk(it, depth + 1)
            else:
                title = getattr(it, "title", str(it))
                print(f"{'  ' * depth}{page_of(it):>4}  {title}")

    outline = getattr(reader, "outline", None) or getattr(reader, "outlines", [])
    walk(outline)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
