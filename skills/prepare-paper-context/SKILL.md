---
name: prepare-paper-context
description: Normalize a paper input (PDF, LaTeX source, multi-file LaTeX project, or pre-extracted text) into a clean structured representation that downstream Proofreader skills can consume. Use this once at the start of any non-trivial Proofreader session so the audit, counterexample, defender, and writeup skills don't each re-parse the source. Especially useful for LaTeX projects, where it preserves theorem-environment fidelity that PDF extraction loses. Triggers on "prepare this paper", "set up context for my .tex source", "extract theorems from this project", or when the user supplies a .tex / project root.
version: 0.1.0
---

# Skill: Prepare Paper Context

## Role

You are the input-normalization stage for the Proofreader plugin. Your job is to take a paper in whatever form the user supplies — a PDF, a single `.tex` file, a multi-file LaTeX project, or already-extracted text — and produce a clean structured representation that downstream skills (`evaluate-paper`, `audit-proof`, `find-counterexample`, etc.) can use without re-parsing.

This skill is most valuable for **LaTeX sources**, where it preserves theorem-environment fidelity, label/ref topology, and math-symbol accuracy that PDF extraction loses. For PDFs it's still useful as a one-time extraction so downstream calls don't re-extract.

## Why LaTeX source beats PDF extraction

When the author has the `.tex` source (their own paper or a coauthor's), use it instead of the PDF whenever possible:

- **Theorem environments are explicit.** `\begin{theorem}[Optional Title]\label{thm:foo}...\end{theorem}` blocks have unambiguous boundaries. PDF extraction guesses these from formatting cues and often gets them wrong.
- **Math symbols are exact.** LaTeX gives you `\sum_{i=1}^n C_i / T_i` verbatim. PDF extraction often produces `Σ Ci /Ti` or worse.
- **Cross-references are mechanical.** `\ref{thm:foo}` and `\label{thm:foo}` form a bipartite graph; dangling references (a documented true-positive flaw pattern) become trivial to detect — just diff the two sets.
- **Bibliography is structured.** `\bibitem` / `.bib` entries are machine-readable.
- **Patches are possible.** With LaTeX source available, the [`annotate-latex`](../annotate-latex/SKILL.md) skill can produce in-place review annotations.

## When PDF is the natural input

For retrospective audits of an author's own already-published work, the LaTeX source is often no longer accessible — the paper exists only as a PDF in the venue's proceedings, sometimes years or decades after submission. This is the expected case for that workflow, not a fallback. PDF extraction is lossier than LaTeX parsing, but the downstream audit skills are calibrated to consume it.

The discipline in this case is to make the loss *visible* rather than hide it:

- Surface extraction warnings prominently in the output — mangled equations, ambiguous theorem boundaries, lost cross-references, unparsed tables.
- For any theorem whose statement looks math-heavy or notation-dense, flag it for the author to verify against the published PDF before trusting downstream verdicts.
- When the bibliography is not cleanly recovered (common for older two-column PDFs), do not invent citations — record what you have and note that the bibliography section is partial.

Downstream skills will treat extraction warnings as a signal to scrutinize affected results more carefully; the audit may end up flagging a result as `uncertain` for extraction reasons rather than substantive reasons, which is the right behavior.

### The dangerous failure mode: silently-plausible extraction errors

The worst extraction errors are not the *obviously* mangled ones (`Σ Ci /Ti`) — those get flagged and scrutinized. The dangerous ones are extractions that come out **clean-looking but wrong**: a `⌈·⌉` ceiling read as a `⌊·⌋` floor, a dropped `+1`, a `≤` read as `<`, a flipped subscript range, a quantifier `∀ℓ>1` read as `∀ℓ>0`. These read as valid math, pass downstream unquestioned, and can manufacture a confident false finding (or hide a real one) because a *single character* in a load-bearing inequality changed.

**Equations and proofs typeset as figures/images are the highest-risk source.** Many RT-systems papers render display equations (and sometimes whole proofs) as embedded images. Text extraction either drops these entirely or returns an OCR-style guess that *looks* like a transcription but was never in the text layer. The reader cannot tell a faithful transcription from a fabricated one.

#### Step 2c (PDF only): detect math-as-figure regions

While extracting, identify equations that are not reliably in the text layer:

- Use PyMuPDF to check, per page, whether equation regions are images: `page.get_images()` and `page.get_drawings()` returning content in the band where a numbered equation should be, with little or no adjacent extracted text, is the tell.
- Cross-check equation **labels**: if the prose references `Eq. (10)` / `Equation (10)` but no line of extracted text on that page parses as that equation, the equation is almost certainly a figure.
- Treat any `□`/`�`/missing-glyph runs, or display lines that extract as empty/whitespace, as suspect.

For every formal result whose statement or proof **depends on** such an equation, mark it explicitly so downstream skills know not to trust the transcribed formula:

```
**Formula fidelity**: UNVERIFIED — Eq. (10) and the L_i definition (Eq. 9) are
typeset as figures; the transcription below is a guess. Any verdict that turns
on the exact form of this equation MUST be re-checked by reading the PDF page
as an image (Read the PDF with `pages: <n>`) before it is trusted.
```

Do **not** silently emit a transcription as if it were faithful. A wrong-but-plausible formula passed downstream is worse than an honest "could not read this — open page N."

## Inputs

One of:
1. A path to a single `.tex` file.
2. A path to the **main** `.tex` file of a multi-file project (the one with `\documentclass`).
3. A path to a PDF.
4. A directory containing a paper (auto-detect: prefer main `.tex` if present, else look for a PDF).
5. Already-extracted text supplied directly.

Optionally: a path to a `.bib` file if the bibliography is external.

## Process

### Step 1: Identify the input format

Inspect the supplied path:
- Ends in `.tex`? → LaTeX single file or main file. Read it; check for `\input{}` / `\include{}` / `\subfile{}` directives.
- Ends in `.pdf`? → PDF. Probe extractors in order (`pymupdf4llm`, `pymupdf`, `pdftotext`) — see Step 2's PDF branch for the exact probe and the reporting requirements.
- A directory? → scan for `main.tex` / `paper.tex` / `<dirname>.tex`. If no main `.tex`, fall back to the largest PDF.
- Plain text? → assume already extracted; skip extraction.

### Step 2: Extract paper text

**For LaTeX**:
- Resolve `\input{}`, `\include{}`, and `\subfile{}` directives recursively. Concatenate into one logical document, preserving file boundaries for error reporting.
- Strip LaTeX comments (`%` to end of line) unless they're in verbatim environments. Preserve any `% PROOFREADER` comments from previous `annotate-latex` runs separately for the user to re-review.
- Resolve `\newcommand` / `\def` macros that the document defines (best-effort; if a macro is complex, leave the call site intact and note this).
- Keep theorem-like environments verbatim, with their labels.

**For PDF**:
- **Probe extractors in order and record which one was used.** This is required output — the user needs to know which fidelity tier produced their context.
  1. `python -c "import pymupdf4llm"` — *preferred.* Markdown-structured output preserves headings, lists, and tables.
  2. `python -c "import pymupdf"` (a.k.a. `fitz`) — acceptable fallback. Plain text, no structure preservation.
  3. `pdftotext --version` (poppler-utils) — last-resort fallback. Loses the most layout information.
- Use the first one that imports/runs successfully. Always set the `**PDF extractor**` field of the output to one of `pymupdf4llm` | `pymupdf` | `pdftotext`, and **if the active extractor is not `pymupdf4llm`, add an extraction warning of the form**:
  > `pymupdf4llm` is the preferred PDF extractor but is not installed in this environment; falling back to `<tool>`. Install with `pip install pymupdf4llm` and re-run for better math/table fidelity.
- If none of the three are available, stop and tell the user: "No PDF extractor available — install one of `pymupdf4llm` (preferred), `pymupdf`, or `pdftotext` (poppler-utils) and re-run."
- Extract text. Note: math notation will be approximate. Flag any obviously-mangled equations.
- Heuristically section-detect (most papers have numbered sections; treat all-caps or bold lines as candidate section headers).
- Identify theorem-like blocks by formatting cues ("Theorem 3.", "Lemma 2.1", italic statement followed by "Proof.").

### Step 2a (LaTeX only): consume `.aux` if present

If the paper has been compiled recently and a sibling `.aux` file exists (e.g., `paper.tex` next to `paper.aux`), parse it to enrich the label topology with rendered-page numbers:

- `\newlabel{thm:foo}{{3}{5}{...}}` → label `thm:foo` is Theorem 3 on rendered page 5. Surface this in the label/ref topology table.
- `\bibcite{baruah2020}{2}` → citation key `baruah2020` is `[2]` in the rendered bibliography. Useful for matching citations in the prose ("see [2]") back to bibliography entries.

If no `.aux` exists, omit the rendered-page column from the topology and note this in extraction warnings. Do **not** invoke `pdflatex` to generate one — that introduces a build dependency outside this skill's scope.

### Step 2b (LaTeX only): parse bibliography

Locate the paper's bibliography:

- Inline `\begin{thebibliography}...\end{thebibliography}` block: parse `\bibitem[<label>]{<key>}` entries; for each, extract author, title, venue, year, URL, DOI from the free-text content (heuristic but workable).
- External `.bib` file referenced by `\bibliography{file}` or `\addbibresource{file.bib}`: parse the `.bib` directly using standard BibTeX entry syntax.
- For papers cited via `\cite{key}`, `\citet{key}`, `\citep{key}`: associate the in-text citation with the bibliography entry.

For each cited entry, record whether the paper is *invoked* (cited but the result is used without restatement: *"by Liu-Layland's theorem"*) or *restated* (the result is reproduced verbatim or paraphrased in the paper's own theorem environment). Restatements are flagged for the [`verify-restatement`](../../agents/verify-restatement.md) agent to consider for cross-paper verification.

Detect restatements by these signals:
- `\begin{theorem}[<Citation>]` or `\begin{lemma}[<Citation>]` — the optional argument names a prior source.
- Italic "Theorem N (Author Year)." or "Lemma N ([Smith 2003])." pattern in the prose immediately before the theorem block.
- Explicit phrasing like "We restate the following result from \cite{key}".

### Step 3: Build the structured representation

Output the following as a Markdown document:

```markdown
# Paper context: <title>

**Source format**: pdf | latex_single | latex_project | text
**Source path**: <path>
**PDF extractor**: pymupdf4llm | pymupdf | pdftotext  *(PDF inputs only; omit for LaTeX/text. Annotate with "(preferred)" or "(fallback — `pymupdf4llm` not installed)" as applicable.)*
**Title**: <title, parsed from \title{} or PDF metadata or first heading>
**Authors**: <list, parsed from \author{} or PDF metadata>

## Sections

- 1. Introduction (lines L1–L2)
- 2. System Model (lines L3–L4)
- …

## Formal results

For each theorem-like environment:

### thm:foo — Theorem 3 (Section 4.1)
- **Type**: theorem | lemma | corollary | proposition | definition
- **Label**: thm:foo (LaTeX) or "Theorem 3" (PDF)
- **Statement**: <verbatim>
- **Formula fidelity**: verified (LaTeX source) | text-extracted (plausible) | UNVERIFIED (equation typeset as figure — read PDF page N as image before trusting) — name the at-risk equation(s) and page
- **Proof present**: yes | no | deferred_to_appendix | cited_to_prior_work
- **Proof text**: <verbatim, if present>

## Label / ref topology

| Label | Defined at | Referenced at |
|---|---|---|
| thm:foo | paper.tex:142 (rendered page 5) | paper.tex:89, 203, 305 |
| eq:bound | paper.tex:167 (rendered page 6) | paper.tex:168, 210 |

**Unresolved references** (referenced but not yet defined):
- `lem:gap` referenced at paper.tex:204, no matching `\label` in the current source.

*Note: unresolved references are recorded here for the author's awareness but are NOT treated as flaws by Proofreader. In active drafting, unresolved refs are routine (a forward reference to a not-yet-written lemma, a holdover from a previous revision, a placeholder). The audit skills will not surface these as findings.*

**Unused labels** (defined but never referenced): informational only.

## Bibliography

For each `\bibitem` / `.bib` entry that is `\cite`-d in the body:

| Citation key | Title | Authors | Venue / year | URL or DOI |
|---|---|---|---|---|
| baruahFL2020 | Schedulability analysis using ILP | Baruah | RTNS 2020 | https://doi.org/... |
| liuLayland1973 | Scheduling algorithms for multiprogramming in a hard-real-time environment | Liu, Layland | JACM 1973 | https://doi.org/... |

If the paper restates a theorem from a cited source (`Theorem 1 (Liu-Layland)`), record the restatement → citation pairing here. The [`verify-restatement`](../../agents/verify-restatement.md) agent uses this list to fetch cited sources and double-check the restatement matches the original.

## Restatements

When the paper restates a theorem/lemma from prior work (typically signaled by `\begin{theorem}[<Citation>]` or by an in-text *"Theorem (Liu-Layland)"*):

| Restated label | Cited as | Citation key | Citation type | Worth verifying? |
|---|---|---|---|---|
| thm:liu-layland-utility-bound | Liu-Layland 1973 | liuLayland1973 | restatement (verbatim or paraphrase of original) | yes if a fetchable source exists |
| thm:dbf-bound | Baruah 2003 | baruah2003 | invocation (used but not restated) | no — invocation only |

Restatements are the high-leverage targets for cross-paper verification: a paper that subtly changes a precondition while restating a known result can propagate the change as if it were the original.

## Notation table

If the paper has an explicit notation table, extract verbatim. Otherwise, infer from theorem statements and provide a best-effort table.

## Extraction warnings

Issues encountered during parsing — useful for the user to know which fidelity to trust:
- "Multi-file project: 3 files resolved, 1 file (`extras.tex`) not found"
- "Equation 5 contains a complex macro `\sched` that could not be expanded automatically"
- "PDF extraction: theorem block at page 7 has unusual formatting; manually verify"
- "PDF extraction: Eq. (9) and (10) on page 7 are typeset as figures — transcription is a guess, Formula fidelity = UNVERIFIED for Theorem 10 and Lemma 15; read page 7 as an image before trusting any floor/ceiling/±1 in those equations"
- "No `.aux` file found at `paper.aux`; rendered page numbers omitted from label topology"
- "`pymupdf4llm` is the preferred PDF extractor but is not installed; falling back to `pymupdf`. Install with `pip install pymupdf4llm` for better math/table fidelity." *(omit this warning entirely when `pymupdf4llm` is the active extractor)*
```

### Step 4: Persist (optional)

If the user requests it, save the structured representation to `<paper-stem>.context.md` so subsequent skill invocations can `Read` it without re-running this skill.

## Downstream usage

Downstream skills should accept either a path to a paper or a pre-prepared context document:

```text
> Audit Theorem 3 of @my-paper.tex
   # invokes evaluate-paper which calls prepare-paper-context first

> Audit Theorem 3 from @my-paper.context.md
   # skips prepare-paper-context; uses the pre-extracted representation directly
```

## Tooling notes

- `pymupdf4llm` is preferred for PDF extraction because it preserves Markdown-like structure (headings, lists, tables). Falls back to `pymupdf` if `pymupdf4llm` isn't installed; falls back to `pdftotext` from poppler-utils if neither is available. Install the preferred extractor with `pip install pymupdf4llm`.
- Always report the active extractor in the output's `**PDF extractor**` field, and surface a clear extraction warning when falling back so the user knows to install `pymupdf4llm` for higher fidelity.
- LaTeX extraction is straight text processing — no external tools required.
- Multi-file project resolution uses simple text substitution; doesn't run `pdflatex`. If a `.aux` file is present, you may consult it for label/page-number mapping but it's not required.
