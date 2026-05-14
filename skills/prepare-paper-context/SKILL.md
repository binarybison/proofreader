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
- Ends in `.pdf`? → PDF. Extract via `pymupdf4llm` if available, else `pymupdf`, falling back to plain `pdftotext` only as last resort.
- A directory? → scan for `main.tex` / `paper.tex` / `<dirname>.tex`. If no main `.tex`, fall back to the largest PDF.
- Plain text? → assume already extracted; skip extraction.

### Step 2: Extract paper text

**For LaTeX**:
- Resolve `\input{}`, `\include{}`, and `\subfile{}` directives recursively. Concatenate into one logical document, preserving file boundaries for error reporting.
- Strip LaTeX comments (`%` to end of line) unless they're in verbatim environments.
- Resolve `\newcommand` / `\def` macros that the document defines (best-effort; if a macro is complex, leave the call site intact and note this).
- Keep theorem-like environments verbatim, with their labels.

**For PDF**:
- Extract text. Note: math notation will be approximate. Flag any obviously-mangled equations.
- Heuristically section-detect (most papers have numbered sections; treat all-caps or bold lines as candidate section headers).
- Identify theorem-like blocks by formatting cues ("Theorem 3.", "Lemma 2.1", italic statement followed by "Proof.").

### Step 3: Build the structured representation

Output the following as a Markdown document (or JSON if the orchestrator requests it):

```markdown
# Paper context: <title>

**Source format**: pdf | latex_single | latex_project | text
**Source path**: <path>
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
- **Proof present**: yes | no | deferred_to_appendix | cited_to_prior_work
- **Proof text**: <verbatim, if present>

## Label / ref topology

| Label | Defined at | Referenced at |
|---|---|---|
| thm:foo | line 142 | lines 89, 203, 305 |
| eq:bound | line 167 | lines 168, 210 |

**Dangling references** (referenced but not defined):
- `lem:gap` referenced at line 204, no matching \label. *(LaTeX source only — this is a likely-true-positive flaw signal.)*

**Unused labels** (defined but never referenced): just informational; not a flaw.

## Bibliography

For each `\bibitem` / `.bib` entry that is `\cite`-d in the body:
- Key, title, venue/year, URL or DOI if present.

## Notation table

If the paper has an explicit notation table, extract verbatim. Otherwise, infer from theorem statements and provide a best-effort table.

## Extraction warnings

Issues encountered during parsing — useful for the user to know which fidelity to trust:
- "Multi-file project: 3 files resolved, 1 file (`extras.tex`) not found"
- "Equation 5 contains a complex macro `\sched` that could not be expanded automatically"
- "PDF extraction: theorem block at page 7 has unusual formatting; manually verify"
```

### Step 4: Persist (optional)

If the user requests it, save the structured representation to `<paper-stem>.context.md` (or `.json`) so subsequent skill invocations can `Read` it without re-running this skill.

## Downstream usage

Downstream skills should accept either a path to a paper or a pre-prepared context document:

```text
> Audit Theorem 3 of @my-paper.tex
   # invokes evaluate-paper which calls prepare-paper-context first

> Audit Theorem 3 from @my-paper.context.md
   # skips prepare-paper-context; uses the pre-extracted representation directly
```

## Tooling notes

- `pymupdf4llm` is preferred for PDF extraction because it preserves Markdown-like structure (headings, lists, tables). Falls back to `pymupdf` if `pymupdf4llm` isn't installed; falls back to `pdftotext` from poppler-utils if neither is available.
- LaTeX extraction is straight text processing — no external tools required.
- Multi-file project resolution uses simple text substitution; doesn't run `pdflatex`. If a `.aux` file is present, you may consult it for label/page-number mapping but it's not required.
