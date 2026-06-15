#!/usr/bin/env python3
"""Generate chapter .qmd skeletons + the _quarto.yml chapter list from outline.txt.

Each top-level outline entry becomes one chapter file under chapters/. Descendant
entries become nested Markdown headings (level = depth+1, capped at 6), each tagged
with an HTML comment giving the source PDF page so transcription can find the text in
assets/raw/text/pageNNN.txt and the visual in assets/raw/pages/pageNNN.png.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTLINE = ROOT / "assets/raw/outline.txt"
CHAP_DIR = ROOT / "chapters"

# Top-level chapters grouped into book parts (title -> part). Order follows the PDF.
PARTS = [
    ("Core Rules", ["Introduction", "The Basics", "The Pretender", "Units",
                     "Movement", "Combat", "Magic", "Dominion"]),
    ("Nations", ["The Origins of Nations"]),
    ("Magic Reference", ["Magic Items", "Path Boosters", "Battlefield Spells",
                          "Summoning Rituals", "Global Enchantments", "Other Rituals"]),
    ("Nation Index", ["Nation Index"]),
    ("Appendix", ["Launch Options"]),
]


def parse():
    """Return flat list of (depth, page, title)."""
    out = []
    for ln in OUTLINE.read_text().splitlines():
        m = re.match(r"^( *)(\d+)  (.*)$", ln)
        if not m:
            continue
        lead, page, title = len(m.group(1)), int(m.group(2)), m.group(3).strip()
        depth = (lead + len(m.group(2)) - 4) // 2
        out.append((max(depth, 0), page, title))
    return out


def slug(title):
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s


def main():
    entries = parse()
    # indices of top-level (depth 0) entries, skipping the cover "Manual Dominions 6"
    tops = [(i, e) for i, e in enumerate(entries) if e[0] == 0]
    files = {}  # title -> filename
    order = 0
    for n, (idx, (_, page, title)) in enumerate(tops):
        if title.startswith("Manual Dominions"):
            continue
        order += 1
        fname = f"{order:02d}-{slug(title)}.qmd"
        files[title] = fname
        # collect descendants until next depth-0 entry
        body = [f"# {title}\n", f"<!-- source: PDF p.{page} -->\n"]
        j = idx + 1
        while j < len(entries) and entries[j][0] != 0:
            d, pg, t = entries[j]
            level = min(d + 1, 6)
            body.append(f"{'#' * level} {t}\n")
            body.append(f"<!-- p.{pg} -->\n")
            j += 1
        body.append("\n::: callout-note\nTranscription pending.\n:::\n")
        (CHAP_DIR / fname).write_text("\n".join(body))

    # emit _quarto.yml chapter block
    print("  chapters:")
    print("    - index.qmd")
    for part_title, titles in PARTS:
        print(f"    - part: \"{part_title}\"")
        print("      chapters:")
        for t in titles:
            if t in files:
                print(f"        - chapters/{files[t]}")
            else:
                sys.stderr.write(f"WARN: part chapter not found in outline: {t}\n")
    # sanity: any top-level not placed in a part?
    placed = {t for _, ts in PARTS for t in ts}
    for t in files:
        if t not in placed:
            sys.stderr.write(f"WARN: chapter not assigned to a part: {t}\n")


if __name__ == "__main__":
    main()
