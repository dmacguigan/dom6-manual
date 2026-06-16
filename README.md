# Dominions 6 Manual (web edition)

An unofficial, searchable web edition of the [Dominions 6 manual](https://www.illwinter.com/dom6/dom6manual.pdf),
built as a [Quarto](https://quarto.org) book and deployed to GitHub Pages.

Access the manual website [here](https://dmacguigan.github.io/dom6-manual/).

> Dominions 6 and its manual are the property of **Illwinter Game Design**. This is a
> fan-made reformatting and is not affiliated with or endorsed by Illwinter.

## Build locally

```bash
quarto preview      # live preview with hot reload
quarto render       # build static site into _book/
```

## Regenerate source material

The PDF and extracted reference material are gitignored and regenerated on demand:

```bash
scripts/extract.sh          # download PDF -> assets/raw/{text,pages,images}, outline.txt
python3 scripts/build_skeleton.py   # (re)generate chapter skeletons from the outline
```

Extraction outputs (all under `assets/raw/`, used only as transcription source):

- `text/pageNNN.txt`  -- `pdftotext -layout` per page (the text to transcribe from)
- `pages/pageNNN.png` -- 150 dpi render of each page (visual reference for layout/tables)
- `images/img-*.png`  -- embedded figures/sprites to curate into `images/`
- `outline.txt`       -- the PDF bookmark tree (drives chapter/section structure)

## Transcription workflow

Each chapter under `chapters/` starts as a skeleton: the real heading hierarchy from the
manual, with `<!-- p.NN -->` comments pointing at the source page. To transcribe a section:

1. Open the matching `assets/raw/text/pageNNN.txt` (and the `pages/pageNNN.png` image if
   the layout is unclear, e.g. multi-column or tables).
2. Replace the `::: callout-note Transcription pending :::` block with clean Markdown.
3. Turn stat blocks / spell / item / unit lists into **Markdown tables**, not raw text.
4. Pull any referenced figure from `assets/raw/images/` into `images/` and embed it with
   `![caption](../images/foo.png){#fig-foo}`.
5. Preserve game terminology exactly; fix only extraction artifacts (hyphenation, column
   bleed, ligatures).
6. `quarto render` and spot-check against the PDF page.

The DRN section in `chapters/02-the-basics.qmd` is a worked example of the prose+table
pattern.

