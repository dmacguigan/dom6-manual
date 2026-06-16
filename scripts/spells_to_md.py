#!/usr/bin/env python3
"""Convert fixed-width battlefield/ritual spell tables to Markdown.

Columns: School | Spell Name | Path | Fat | Rng | AoE | Pre | Dmg | NoE | Special.
Page-independent: spell rows are detected by a leading "<School> <level>" prefix;
indented lines are continuations (summoned-creature stat blocks, wrapped spell
names, or wrapped Special text) and are folded into the spell's row.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPLIT = re.compile(r"\s{2,}")
SCHOOLROW = re.compile(r"^(?:Conj|Alt|Evo|Const|Ench|Thaum?|Blood|Div)\s+\d+\s{2,}\S")
CREATURE = re.compile(r"^(.+?\sx\d+\+?)\s+(HP\b.*)$")


def md(cell):
    return cell.replace("|", r"\|").strip()


def main(first, last):
    out = []
    rows = []
    cols = []
    in_table = False
    pending_title = None
    title_emitted = set()

    def flush():
        nonlocal rows, in_table
        if rows and cols:
            out.append("| " + " | ".join(cols) + " |")
            out.append("|" + "|".join("---" for _ in cols) + "|")
            for r in rows:
                r = (r + [""] * len(cols))[: len(cols)]
                out.append("| " + " | ".join(md(c) for c in r) + " |")
            out.append("")
        rows = []
        in_table = False

    def append_special(text):
        if len(rows[-1]) < len(cols):
            rows[-1].extend([""] * (len(cols) - len(rows[-1])))
        rows[-1][-1] = (rows[-1][-1] + " " + text).strip()

    for p in range(first, last + 1):
        f = ROOT / f"assets/raw/text/page{p:03d}.txt"
        if not f.exists():
            continue
        for raw in f.read_text().splitlines():
            line = raw.rstrip()
            s = line.strip()
            if not s or s.isdigit():
                continue
            indented = raw[:1] == " "
            # column header
            if s.startswith("School") and ("Spell Name" in s or "Ritual Name" in s):
                flush()
                cols = SPLIT.split(s)
                in_table = True
                if pending_title and pending_title not in title_emitted:
                    out.append(f"## {pending_title}\n")
                    title_emitted.add(pending_title)
                pending_title = None
                continue
            # spell row
            if not indented and SCHOOLROW.match(line):
                rows.append(SPLIT.split(s))
                continue
            # continuation lines (only meaningful inside a table)
            if indented and in_table and rows:
                m = CREATURE.match(s)
                if m:
                    append_special(f"Summons {m.group(1)}: {m.group(2)}")
                elif (
                    "," not in s and ":" not in s and len(s) <= 22
                    and rows[-1][-1:] == [""]  # special still empty -> name wrap
                ):
                    rows[-1][1] = (rows[-1][1] + " " + s).strip()
                else:
                    append_special(s)
                continue
            # otherwise a section-title candidate
            if not indented and not s.startswith(("key", "Path ", "F /", "S /", "B/")):
                pending_title = s
    flush()
    print("\n".join(out))


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
