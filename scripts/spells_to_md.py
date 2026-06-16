#!/usr/bin/env python3
"""Convert fixed-width battlefield/ritual spell tables to HTML tables.

Columns: School | Spell Name | Path | Fat | Rng | AoE | Pre | Dmg | NoE | Special.
Page-independent: spell rows are detected by a leading "<School> <level>" prefix.
Indented continuation lines (summoned-creature stat blocks and prose effect
descriptions) are emitted as a full-width description row *beneath* the spell,
mimicking the manual's layout. Short flags that share the spell's own line stay
in the Special column. Wrapped spell names are merged back into the name.
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPLIT = re.compile(r"\s{2,}")
SCHOOLROW = re.compile(r"^(?:Conj|Alt|Evo|Const|Ench|Thaum?|Blood|Div)\s+\d+\s{2,}\S")
CREATURE = re.compile(r"^(.+?\sx\d+\+?)\s+(HP\b.*)$")


def esc(c):
    return html.escape(c.strip())


def main(first, last):
    out = []
    rows = []  # each: [cells_list, desc_str]
    cols = []
    in_table = False
    pending_title = None
    title_emitted = set()

    def flush():
        nonlocal rows, in_table
        if rows and cols:
            n = len(cols)
            out.append("```{=html}")  # raw passthrough so colspan/classes survive
            out.append('<table class="table spell-table">')
            out.append("<thead><tr>" + "".join(f"<th>{esc(c)}</th>" for c in cols) + "</tr></thead>")
            out.append("<tbody>")
            for cells, desc in rows:
                cells = (cells + [""] * n)[:n]
                out.append("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in cells) + "</tr>")
                if desc.strip():
                    out.append(f'<tr class="spell-desc"><td colspan="{n}">{esc(desc)}</td></tr>')
            out.append("</tbody></table>")
            out.append("```")
            out.append("")
        rows = []
        in_table = False

    def add_desc(text):
        rows[-1][1] = (rows[-1][1] + " " + text).strip()

    def add_special(text):
        cells = rows[-1][0]
        if len(cells) < len(cols):
            cells.extend([""] * (len(cols) - len(cells)))
        cells[-1] = (cells[-1] + " " + text).strip()

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
                rows.append([SPLIT.split(s), ""])
                continue
            # continuation lines (only meaningful inside a table)
            if indented and in_table and rows:
                m = CREATURE.match(s)
                if m:  # summoned-creature stat block -> description row
                    add_desc(f"Summons {m.group(1)}: {m.group(2)}")
                elif "," not in s and ":" not in s and len(s) <= 22 and not rows[-1][1]:
                    add_special(s)  # short wrapped flag/name -> Special column
                else:
                    add_desc(s)  # prose description -> description row
                continue
            # otherwise a section-title candidate
            if not indented and not s.startswith(("key", "Path ", "F /", "S /", "B/")):
                pending_title = s
    flush()
    print("\n".join(out))


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
