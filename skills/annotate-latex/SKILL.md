---
name: annotate-latex
description: Inject Proofreader audit findings as in-place annotations into the paper's LaTeX source, so the author can review and address them inside their normal editor workflow. Produces a unified diff (or applies the edits directly with permission), using \todo{} for visible margin notes if the paper supports them, falling back to PROOFREADER comments otherwise. Triggers on "annotate my LaTeX with the findings", "add todo comments for these audits", "patch my .tex with the audit results".
version: 0.1.0
---

# Skill: Annotate LaTeX

## Role

You take Proofreader audit findings (and optionally counterexample / stress-test / writeup outputs) and inject them into the paper's `.tex` source as in-place annotations. The author then sees the findings in their editor next to the actual proof text, can address them in a normal revision pass, and can `git diff` to track what changed.

This is the *opposite* end of [`prepare-paper-context`](../prepare-paper-context/SKILL.md): that one reads source in, this one writes annotations back out.

## Why this exists

Markdown audit reports are great for one-shot review but poor for revision. When the author opens their `.tex` source in their editor, they want to see *"this proof has a problem"* next to the proof, not in a separate document. Author-mode tools like `\todo{}` from `todonotes` are designed for exactly this.

## Inputs

Required:
1. **Paper source** — path to the `.tex` file (or main file of a project) you want to annotate.
2. **Audit findings** — output of `audit-proof` (or `/proofread`'s findings list). One result per audit.

Optional:
3. **Counterexample report** — to annotate the proof with the counterexample summary.
4. **Stress-test verdict** — to suppress annotations for `false_positive` findings (the user has decided these aren't real).
5. **Writeup briefs** — to attach to each annotation a `\todo{...}` pointing at the corresponding writeup file.

## Annotation styles

Detect what the paper already uses and adapt. In priority order:

### Style 1: `\todo{}` from `todonotes` (preferred)

If the paper's preamble has `\usepackage{todonotes}` or `\usepackage[options]{todonotes}`, use:

```latex
\todo[color=red!30]{\textbf{Proofreader audit}: <one-line summary>. \textit{See} \texttt{finding-thm-3.md}.}
```

These render as visible margin notes when the paper is built.

### Style 2: Manual `\todo` macro

If the paper defines its own `\todo` or `\note` macro (look for `\newcommand{\todo}`), use that macro instead. Don't introduce a package the author hasn't opted into.

### Style 3: PROOFREADER comments (fallback)

If neither `todonotes` nor a custom todo macro is present, use plain LaTeX comments:

```latex
% PROOFREADER [moderate]: <one-line summary>
% PROOFREADER:   Issue type: dependency_error
% PROOFREADER:   See finding-thm-3.md for the full audit.
```

These are invisible in the rendered PDF but visible in the editor and in `git diff`.

Never insert anything that would change the rendered output without the user's explicit consent. The `\todo{}` margin notes are an exception only when `todonotes` is already in the preamble (the author opted in).

## Placement rules

Place each annotation immediately **after** the `\begin{...}` line of the environment it applies to, or immediately after the labeled equation. This keeps `git diff` minimal — the annotation lands at a line near the proof, not scattered through it.

For a theorem with an audit finding:

```latex
\begin{theorem}\label{thm:foo}
\todo{\textbf{Proofreader}: incorrect-formula issue at step 3. See finding-thm-3.md.}
<theorem statement>
\end{theorem}
\begin{proof}
\todo{\textbf{Proofreader}: load-bearing step on line 4 substitutes R^- where R^+ is required.}
<proof body>
\end{proof}
```

For an equation with a finding:

```latex
\begin{equation}\label{eq:bound}
% PROOFREADER [moderate]: constant gamma assumed = 1; Table 2 shows gamma up to 1.095.
R_i \leq C_i + \sum_j B_j
\end{equation}
```

## Process

### Step 1: Match findings to source locations

For each audit finding, look up the targeted result's label and find the corresponding `\label{}` in the `.tex` source. If the audit was done on a PDF, you'll have a result number ("Theorem 3") but no label — search for `\begin{theorem}` blocks and match by number (count occurrences) or by statement-text similarity.

### Step 2: Determine annotation style

Inspect the preamble for `\usepackage{todonotes}` or `\newcommand{\todo}`. If neither is present, use Style 3 (PROOFREADER comments).

If `todonotes` is missing but the user explicitly requests `\todo{}` annotations, ask for permission to add `\usepackage{todonotes}` to the preamble. Do NOT add it without permission.

### Step 3: Compose the annotations

For each finding, compose a one-line summary plus a pointer to the full writeup (if one exists). Include severity, issue type, and (if a counterexample exists) the discrepancy magnitude.

### Step 4: Output as a unified diff

Produce a unified diff against the original source:

```diff
--- a/paper.tex
+++ b/paper.tex
@@ -141,6 +141,7 @@
 \begin{theorem}\label{thm:foo}
+\todo[color=red!30]{\textbf{Proofreader}: incorrect-formula on step 3. See finding-thm-3.md.}
 For any task set $\tau$ satisfying ...
```

Present the diff to the user, then ask whether to apply it (`yes` / `no` / `show full diff`). On `yes`, apply with `Edit` (or write the patched file alongside the original as `paper.annotated.tex`).

### Step 5: Index file

After applying annotations, write an `annotations-index.md` next to the paper:

```markdown
# Proofreader annotations on <paper>

Annotations applied on <ISO date>:

| Location | Severity | Type | Finding brief |
|---|---|---|---|
| `\label{thm:foo}` (line 141) | moderate | incorrect_formula | finding-thm-3.md |
| `\label{eq:bound}` (line 167) | minor  | notation_ambiguity | finding-eq-bound.md |

To remove all Proofreader annotations: `sed -i '/PROOFREADER/d' paper.tex` (for Style 3), or remove the `\todo{}` lines via a `git diff` review.
```

## What this skill does *not* do

- **Compile the paper.** That's the author's job. If they want to verify a proposed annotation doesn't break compilation, they `pdflatex` it themselves.
- **Rewrite proofs.** Annotations point at issues; the author rewrites. (A future `propose-proof-patch` skill could do this; not yet built.)
- **Modify the rendered PDF.** Annotations that affect rendered output (`\todo{}` margins) are only added when the paper already opts into them.
- **Touch files the user didn't authorize.** Annotation always goes through a diff review unless the user explicitly opts into auto-apply.

## Removing annotations

Document how the user undoes annotations:

- **Style 1 / 2 (\todo)**: `git diff` and revert; or `sed -i '/\\\\todo\\[color=red.30\\]{\\\\textbf{Proofreader/d' paper.tex` for the specific style.
- **Style 3 (PROOFREADER comments)**: `sed -i '/% PROOFREADER/d' paper.tex` removes all of them.

After a successful revision pass, the author should remove annotations they've addressed; the index file is the canonical list.
