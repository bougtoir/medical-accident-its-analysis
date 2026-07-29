# Beyond the Calculus of Lives

A philosophical essay project on the ethics of weighing lives, taking the
atomic bombing of Japan as its point of departure and building toward a
diagnosis of the civilizational roots of total war and its deterrence.

## Central thesis

The question "was the atomic bombing necessary?" is asked *inside* a calculus;
the deeper question is whether human beings are entitled to weigh and decide
who lives and who dies at all. The essay argues that (1) the utilitarian
justification presupposes a commensurability of lives that value pluralism
gives us reason to deny; (2) since finitude makes some choosing unavoidable,
the moral line falls not on the *outcome* of a weighing but on its *attitude*
(the "taking calculus" vs. the "giving calculus"); (3) the drift toward the
sovereign's chair is bound up with a civilizational choice between increasing
supply (expansion/conquest) and reducing demand (contraction/defence); and
(4) deterring a third world war requires not a better calculus but a
disciplined, two-handed (technological and ideational) retreat from it.

## Outputs

Three deliverables, from the same argument:

- **Feature article (English, ~7,100 words, 33 endnotes, 3 figures inline)** —
  the full peer-reviewed version. Primary target *Journal of Military Ethics*
  (hybrid; subscription route = no APC); *Ethics & International Affairs*
  Feature (Gold OA; post-acceptance waiver) as secondary. Eight sections
  including a dedicated §7 "Objections and Replies." Chicago-style
  numbered endnotes, numbered in order of first appearance. The JME submission
  package is built by `scripts/build_submission_jme.py`.
- **Essay (English, ~2,700 words, 8 endnotes, 1 figure)** — condensed from
  the same core argument for the *Ethics & International Affairs* "Essays"
  (non-refereed) category: fast, editor-only review, likely no APC. Title:
  "The Accountants of One Another's Lives."
- **General-audience essay (Japanese)** — to be refined in Japanese and
  translated for submission to an Estonian general-interest magazine
  (e.g. *Vikerkaar* / *Diplomaatia* / *Akadeemia*). Estonian route currently
  on hold.

## Directory layout

```
scripts/
  generate_figures.py      # 3 conceptual figures (PNG + TIFF), English
  create_manuscript_en.py  # manuscript_en.docx (Feature; figures inline, endnotes) + title_page_en.docx
  create_essay_en.py       # essay_en.docx (E&IA Essay; ~2,700 words, 8 notes, fig1 inline)
  create_figures_pptx.py   # figures_en.pptx (editable, one figure per slide)
  create_essay_ja.py       # essay_ja.docx (Japanese general-audience version)
  build_submission_eia.py  # assembles the E&IA Essay submission package (+ zip)
  build_submission_eia_feature.py  # assembles the E&IA Feature submission package (+ zip)
  build_submission_jme.py  # assembles the Journal of Military Ethics submission package (+ zip)
output/
  manuscript_en.docx, title_page_en.docx
  essay_en.docx
  essay_ja.docx
  figures_en.pptx
  fig1_layers.{png,tif}, fig2_quadrant.{png,tif}, fig3_asymptote.{png,tif}
```

## Build

```bash
pip install python-docx python-pptx matplotlib pillow
cd scripts
python generate_figures.py       # figures first (manuscript embeds them)
python create_manuscript_en.py
python create_essay_en.py
python create_figures_pptx.py
python create_essay_ja.py
python build_submission_jme.py
```

## Figures

1. **Two layers of the question** — inner (technical/consequential) vs. outer
   (ethical/existential).
2. **Two independent axes** — supply-increasing vs. demand-reducing, and
   expansion vs. contraction, with illustrative religious/economic types.
3. **Asymptotic model** — raising supply and lowering demand both approach
   bounds (cosmic ceiling; irreducible need) without abolishing scarcity.
