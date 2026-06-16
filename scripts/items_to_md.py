#!/usr/bin/env python3
"""Convert the fixed-width magic-item tables (full-layout pdftotext) to Markdown.

Reads assets/raw/text/pageNNN.txt for a page range, finds each
"<Category>: <Tier> (Construction level N)" section, parses the aligned columns
into a Markdown table, and prints the result. Wrapped continuation lines are
merged into the previous row's last cell. Rows whose second column is not a
magic-path code (e.g. a summoned unit's stat block) are folded into the final
column so they don't corrupt the numeric columns.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPLIT = re.compile(r"\s{2,}")
SECTION = re.compile(r"^(.+?): (.+?) \(Construction level (\d)\)\s*$")
PATHCODE = re.compile(r"^[FAWESDNGBH0-9]+$")
PAGENUM = re.compile(r"^\s*\d{1,3}\s*$")


def md_escape(cell: str) -> str:
    return cell.replace("|", r"\|").strip()


UNITBLOCK = re.compile(r"^(HP|Prot|MR) \d")


def merge_name_wraps(rows):
    """Fold path-less name-wrap continuation rows into the preceding row."""
    merged = []
    for r in rows:
        path = r[1] if len(r) > 1 else ""
        special = r[-1]
        if not path and merged and not UNITBLOCK.match(special):
            merged[-1][0] = (merged[-1][0] + " " + r[0]).strip()
            if special:
                merged[-1][-1] = (merged[-1][-1] + " " + special).strip()
        else:
            merged.append(r)
    return merged


def emit_table(header, rows, out):
    if not header or not rows:
        return
    rows = merge_name_wraps(rows)
    out.append("| " + " | ".join(md_escape(h) for h in header) + " |")
    out.append("|" + "|".join("---" for _ in header) + "|")
    for r in rows:
        # pad/truncate to header width
        r = (r + [""] * len(header))[: len(header)]
        out.append("| " + " | ".join(md_escape(c) for c in r) + " |")
    out.append("")


def main(first, last):
    out = []
    header = None
    rows = []

    def flush():
        nonlocal header, rows
        emit_table(header, rows, out)
        header, rows = None, []

    for p in range(first, last + 1):
        f = ROOT / f"assets/raw/text/page{p:03d}.txt"
        if not f.exists():
            continue
        for raw in f.read_text().splitlines():
            line = raw.rstrip()
            if not line.strip():
                continue
            if PAGENUM.match(line):
                continue
            m = SECTION.match(line.strip())
            if m:
                flush()
                cat, tier, lvl = m.group(1), m.group(2), m.group(3)
                out.append(f"### {cat}: {tier} (Construction level {lvl})\n")
                continue
            cells = SPLIT.split(line.strip())
            # column header row -- split on whitespace, re-join "Special properties"
            if cells and cells[0] == "Name":
                flush()
                toks = line.split()
                if toks[-2:] == ["Special", "properties"]:
                    header = toks[:-2] + ["Special properties"]
                else:
                    header = toks
                continue
            if header is None:
                continue  # prose / preamble lines, skip
            # continuation line (no value in the Name column)
            if raw[:6].strip() == "" and rows:
                rows[-1][-1] = (rows[-1][-1] + " " + line.strip()).strip()
                continue
            # name is reliably separated from the rest by 2+ spaces
            name = cells[0]
            rest = line.strip()[len(name):].strip()
            tokens = rest.split()
            # name with a single-spaced path glued on (e.g. "... Druid N4")
            if not tokens or not PATHCODE.match(tokens[0]):
                nameparts = name.split()
                if len(nameparts) > 1 and PATHCODE.match(nameparts[-1]):
                    tokens = [nameparts[-1]] + tokens
                    name = " ".join(nameparts[:-1])
                    rest = (nameparts[-1] + " " + rest).strip()
            ncol = len(header)
            nstat = ncol - 3  # Name, Path, <nstat stats>, Special properties
            # summoned-unit stat block: no path code at the front
            if not tokens or not PATHCODE.match(tokens[0]):
                rows.append([name] + [""] * (ncol - 2) + [rest])
                continue
            path = tokens[0]
            stats = tokens[1 : 1 + nstat]
            special = " ".join(tokens[1 + nstat :])
            row = [name, path] + stats + [special]
            rows.append(row)
    flush()
    print("\n".join(out))


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
