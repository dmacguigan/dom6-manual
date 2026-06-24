#!/usr/bin/env python3
"""Convert the Nation Index (full-layout pdftotext) to Markdown.

The table of contents on pp.241-242 gives each nation's starting page, which
delimits the entries. Within a nation we emit the descriptive prose, a profile
list (Race/Military/Magic/...), and the recruitable commander/unit tables, whose
two-line entries (Name + cost, then an indented stat block) become table rows.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOC_PAGES = (241, 242)
INDEX_FIRST, INDEX_LAST = 243, 430

TOC_ENTRY = re.compile(r"([A-Z][\w’'.,/&() -]+?)\s+page\s+(\d+)")
UNIT = re.compile(r"^(\S.*?)\s{2,}(Gold\b.*)$")
PROFILE = re.compile(
    r"^(Race|Military|Magic|Priests?|Dominion|Buildings?|Forts?|Recruitment|"
    r"Heat|Cold|Unrest|Special|Income|Bless|Notes|Sacred|Holy|Mages?|Troops?)\s*:\s*(.*)$"
)
SUBTABLE = re.compile(r"(commanders|units|summons|heroes|troops|mercenaries)\s*$", re.I)
PAGENUM = re.compile(r"^\s*\d{1,3}\s*$")


def md(c):
    return c.replace("|", r"\|").strip()


def load_toc():
    entries = []
    for p in TOC_PAGES:
        for line in (ROOT / f"assets/raw/text/page{p:03d}.txt").read_text().splitlines():
            if "page" not in line:
                continue
            for name, pg in TOC_ENTRY.findall(line):
                # drop any left-column junk merged in (separated by 2+ spaces)
                name = re.split(r"\s{2,}", name.strip())[-1].strip()
                if name in ("Early Ages", "Middle Ages", "Late Ages", "Nation Index"):
                    continue
                entries.append((name, int(pg)))
    # de-dup and sort by page
    seen, out = set(), []
    for name, pg in sorted(entries, key=lambda x: x[1]):
        if pg in seen:
            continue
        seen.add(pg)
        out.append((name, pg))
    return out


def page_lines(p):
    f = ROOT / f"assets/raw/text/page{p:03d}.txt"
    return f.read_text().splitlines() if f.exists() else []


def main(first=INDEX_FIRST, last=INDEX_LAST):
    toc = load_toc()
    starts = {pg: name for name, pg in toc}
    out = []
    rows = []  # current unit table rows
    table_open = False
    prose = []

    def flush_prose():
        nonlocal prose
        if prose:
            out.append(" ".join(prose) + "\n")
        prose = []

    def close_table():
        nonlocal rows, table_open
        flush_prose()
        if rows:
            out.append("| Unit | Cost | Stats |")
            out.append("|------|------|-------|")
            for r in rows:
                out.append(f"| {md(r[0])} | {md(r[1])} | {md(r[2])} |")
            out.append("")
        rows = []
        table_open = False

    for p in range(first, last + 1):
        lines = page_lines(p)
        nation_title = starts.get(p)
        for raw in lines:
            line = raw.rstrip()
            s = line.strip()
            if not s or PAGENUM.match(line):
                continue
            indented = raw[:2] == "  "
            # nation heading (matches the TOC title for this page, once)
            if nation_title and s == nation_title:
                close_table()
                out.append(f"## {nation_title}\n")
                nation_title = None
                continue
            # indented stat block -> append to last unit row (else prose continuation)
            if indented:
                if rows:
                    rows[-1][2] = (rows[-1][2] + " " + s).strip()
                elif prose:
                    prose.append(s)
                continue
            # unit entry: "Name   Gold ..., Res ..., Rec ..."
            m = UNIT.match(line)
            if m and not indented:
                rows.append([m.group(1).strip(), m.group(2).strip(), ""])
                table_open = True
                continue
            # sub-table heading (e.g. "X, recruitable commanders")
            if not indented and SUBTABLE.search(s) and "Gold" not in s:
                close_table()
                out.append(f"### {s}\n")
                continue
            # profile line
            pm = PROFILE.match(s)
            if pm and not indented:
                close_table()
                out.append(f"**{pm.group(1)}:** {pm.group(2)}\n")
                continue
            # otherwise prose
            if not indented:
                if rows:
                    close_table()
                prose.append(s)
    close_table()
    print("\n".join(out))


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        main(int(sys.argv[1]), int(sys.argv[2]))
    else:
        main()
