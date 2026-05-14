---
name: annotate-latex
description: Inject Proofreader audit findings as comment-only annotations into the paper's LaTeX source so the author can review them in their editor next to the actual proof text. Output is plain `%` comments that do NOT affect the rendered PDF and do NOT require any new packages. Produces a unified diff for review before applying. Triggers on "annotate my LaTeX with the findings", "add audit comments to my .tex", "patch my source with the audit results".
version: 0.1.0
---

# Skill: Annotate LaTeX

## Role

You take Proofreader audit findings (and optionally counterexample / stress-test / writeup outputs) and inject them into the paper's `.tex` source as **comment-only** annotations. The author sees the findings in their editor next to the affected proof text, can address them in a normal revision pass, and can `git diff` to track what changed.

This is the *opposite* end of [`prepare-paper-context`](../prepare-paper-context/SKILL.md): that one reads source in, this one writes annotations back out.

## Inviolable rules

1. **Comments only.** Every annotation begins with `%` and is a single line. No `\todo{}`, no `\marginpar`, no custom macros, no `\textcolor`, no anything that would render in the compiled PDF.
2. **No package additions.** Never insert `\usepackage{...}` lines. Never modify the preamble.
3. **No content edits.** Never rewrite proof text, theorem statements, or any non-comment lines. The author writes the paper; this skill annotates it.
4. **Diff first, apply on consent.** Always present a unified diff and ask the user before writing the file.
5. **Compile-safe.** A LaTeX file that compiled before this skill ran will compile identically after — the rendered PDF is byte-identical except for the missing annotations.

These rules are not preferences; they are hard constraints. The author may be using this skill mid-draft and any unintended LaTeX-level change risks polluting their build artifacts.

## Why this exists

Markdown audit reports are good for one-shot review but poor for revision. When the author opens their `.tex` source in their editor, they want to see *"this proof has a problem"* near the proof itself, not in a separate document. LaTeX comments are the cleanest way to achieve that without changing what the compiler sees.

## Inputs

Required:
1. **Paper source** — path to the `.tex` file (or main file of a project) you want to annotate.
2. **Audit findings** — output of `audit-proof` (or `/proofread`'s findings list). One result per audit.

Optional:
3. **Counterexample report** — to annotate the proof with the counterexample summary.
4. **Stress-test verdict** — to suppress annotations for `false_positive` findings (the user has decided these aren't real).
5. **Writeup briefs** — so each annotation can reference the corresponding writeup filename.

## Annotation format

Every annotation line begins with `% PROOFREADER` so the entire set can be removed mechanically with a single `sed` invocation.

```latex
% PROOFREADER [<severity>] [<type>]: <one-line summary>
% PROOFREADER:   <continuation, indented two spaces>
% PROOFREADER:   See <finding-brief-filename> for the full audit.
```

Severities: `minor` / `moderate` / `serious` / `critical`.
Types: the issue's `type` field from the audit (`incorrect_formula`, `missing_precondition`, `dependency_error`, etc.).

A typical annotation block is 2–4 lines. Keep them tight — verbose annotations clutter the source and make `git diff` noisy.

### Example

```latex
\begin{theorem}\label{thm:foo}
% PROOFREADER [moderate] [missing_precondition]: theorem statement is missing the "continuously backlogged" precondition.
% PROOFREADER:   Proof of Lemma 6 requires continuous backlog; current statement only requires backlog.
% PROOFREADER:   See finding-thm-foo.md.
For any task set $\tau$ satisfying ...
\end{theorem}
\begin{proof}
% PROOFREADER [serious] [incorrect_formula]: load-bearing step on line 4 substitutes R^- where R^+ is required.
% PROOFREADER:   Inductive chain uses lower bound where upper bound was established. See finding-thm-foo.md.
... proof body ...
\end{proof}
```

For a labeled equation:

```latex
\begin{equation}\label{eq:bound}
% PROOFREADER [moderate] [incorrect_formula]: constant gamma assumed = 1; Table 2 shows gamma reaches 1.095.
R_i \leq C_i + \sum_j B_j
\end{equation}
```

## Placement rules

Place each annotation immediately **after** the `\begin{...}` line of the environment it applies to, or immediately after the labeled equation's `\begin{equation}` / `\begin{align}` line. This keeps `git diff` minimal — annotation lands one line above the affected content.

For findings that target the whole environment (e.g., a theorem with multiple issues), group all related annotations into one block immediately after `\begin{theorem}`. Do not interleave annotations with the theorem statement.

For findings that target a specific equation within a proof, place the annotation immediately above the equation. If the equation is inline (no `\begin{equation}`), place the annotation on the line before the surrounding paragraph and reference the inline location verbally in the annotation text.

## Process

### Step 1: Match findings to source locations

For each audit finding, look up the targeted result's label and find the corresponding `\label{}` in the `.tex` source.

If the audit was done on a PDF (no LaTeX label available), you'll have a result number ("Theorem 3") and a verbatim statement. Search for `\begin{theorem}` blocks; match by:
- Statement-text similarity (preferred — exact phrase matches).
- Ordinal count (the third `\begin{theorem}` in document order if numbering is plain).

If matching is ambiguous, list the candidates and ask the user once.

### Step 2: Compose annotations

For each finding:
- One header line: `% PROOFREADER [<severity>] [<type>]: <one-line summary>`. ≤ 100 characters total. State the *what*, not the why.
- 1–3 continuation lines: `% PROOFREADER:   <detail>` for the why and any quantitative detail.
- One trailing reference line if a finding brief exists: `% PROOFREADER:   See <brief-filename>.`

### Step 3: Produce a unified diff

Present the diff. Do not apply yet.

```diff
--- a/paper.tex
+++ b/paper.tex
@@ -141,6 +141,8 @@
 \begin{theorem}\label{thm:foo}
+% PROOFREADER [moderate] [missing_precondition]: theorem statement omits "continuously backlogged".
+% PROOFREADER:   See finding-thm-foo.md.
 For any task set $\tau$ satisfying ...
```

Ask: *"Apply this diff to paper.tex? (yes / no / show full diff)"*. On `yes`, apply with `Edit`. On `no`, do nothing; the diff itself is the deliverable.

### Step 4: Index file

After applying, write `annotations-index.md` next to the paper:

```markdown
# Proofreader annotations on <paper>

Applied <ISO date>. All annotations are LaTeX comments (`% PROOFREADER ...`)
and do not affect the rendered PDF.

| Location | Severity | Type | Finding brief |
|---|---|---|---|
| `\label{thm:foo}` (paper.tex:141) | moderate | missing_precondition | finding-thm-foo.md |
| `\label{eq:bound}` (paper.tex:167) | moderate | incorrect_formula | finding-eq-bound.md |

To remove ALL Proofreader annotations from this file:
    sed -i '/^% PROOFREADER/d' paper.tex
```

The `sed` removal pattern is anchored to the start of the line (`^%`) to avoid touching any `% PROOFREADER` substring that happens to appear inside a verbatim environment or string literal.

## What this skill does *not* do

- **Compile the paper.** No `pdflatex` invocations.
- **Rewrite proofs.** Annotations point at issues; the author rewrites.
- **Modify the rendered PDF.** All annotations are LaTeX comments.
- **Add packages.** No `\usepackage` insertions, ever.
- **Touch files the user didn't authorize.** Always diff-first.

## Removing annotations

After a successful revision pass, the author should remove annotations they've addressed. The single sed line in the index file removes all annotations at once. For selective removal, `git diff` shows every annotation that was added; the author can revert individual hunks.
