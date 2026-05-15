---
name: writeup-finding
description: Draft a clean, self-contained technical brief documenting a correctness finding — usable to share with coauthors, to record in a project log, or to drop into a paper revision as the basis for a fix. Produces LaTeX or Markdown depending on the user's preference. Use when the user says "write this up", "draft a finding for X", "write a brief on the Theorem N issue", or after `audit-proof` + `find-counterexample` + `stress-test-defense` have produced material to synthesize.
version: 0.1.0
---

# Skill: Writeup Finding

## Role

You are drafting a concise technical brief for a finding produced by the proofreader pipeline. The brief is for the *author's own records* and possibly for sharing with coauthors — not for external publication. Optimize for:

- A coauthor can skim it in 5 minutes and understand the issue.
- A future-you, six months from now, can recover the full context of what was wrong, what evidence supports the finding, and what fix was proposed.

## Format

The user may request **`latex`** (default, suitable for pasting into a paper-revision project) or **`markdown`** (suitable for a project log or GitHub issue). If unspecified, ask.

## Intent and audience

A finding brief can serve several audiences along a spectrum from private to public. The user's intent shapes the tone, the structural emphasis, and how much context the brief duplicates from the paper. Ask once if the intent isn't clear from the conversation:

- **Private note** (default if unstated). Audience: future-you, six months from now. Bias toward complete reasoning even at the cost of redundancy with the audit — the reader is reconstructing context cold. Hedging language is fine where the evidence supports it.
- **Coauthor share.** Audience: people who already know the paper. Compress background. Lead with the broken proof step and the proposed fix. Honest disagreement is welcome — coauthors push back, so present the strongest evidence rather than the most cautious framing.
- **Successor-paper footnote.** Audience: readers of a follow-up paper that builds on the affected result. Explain the issue without alarming readers about the successor's correctness — emphasize what was wrong in the prior paper, what is in fact true, and what specifically depends on the corrected statement going forward.
- **Public errata entry.** Audience: anyone who cites the paper. The brief is the public record. Use restrained, declarative language. Lead with the corrected statement and the date the issue was identified. Avoid speculation about *why* the original was wrong — describe what is, not what should have been.
- **Formal venue erratum.** Audience: program chair / journal editor + the community. Most structured: explicit citation of the affected result; the nature of the error in 1–2 sentences; the corrected statement (with full proof or proof sketch); acknowledgement of the discoverer if external; impact statement on downstream results. Closer in form to a short paper than to a memo.

Tone discipline across the spectrum: as the audience becomes more public, drop hedging language (*"we believe"*, *"appears to"*) in favor of declarative statements where evidence supports them — and conversely, do *not* declare an error you have only inferred. Public-facing briefs that overclaim are worse than private ones that hedge.

The eight-section Document Structure below is the maximum form; private and coauthor briefs may compress or merge sections (e.g., fold Background into Overview), while errata briefs may expand Suggested Fix into a full corrected proof.

## Inputs

Required:
1. **Result label and statement** — e.g. *Theorem 3 of [paper]*.
2. **Audit** — output of `audit-proof`, identifying the specific flaw.

Optional but improves output:
3. **Counterexample** — output of `find-counterexample`, including parameters, paper-vs-correct result, and verification method.
4. **Stress-test verdict** — output of `stress-test-defense`, including any defense considerations and the arbiter's verdict.
5. **Paper bibliography entry** — for the `\cite{}` reference.

## Document Structure

The brief should have these sections, in order. Sections that lack source material may be omitted (e.g. no "Counterexample" section if none was constructed).

### 1. Title and metadata

- **Title**: short, specific description of the issue (not the paper title). E.g. *"Off-by-one in the response-time recurrence of [Paper] Theorem 3"*. Should fit in one line.
- **Author**: the LLM and tool that produced the brief, with a date.

### 2. Overview (1 paragraph)

Lead with the *finding*, not the methodology. State:

- What is wrong.
- Which result is affected.
- **Whether the issue is in the result or only in the proof.** This is a critical distinction. If the audit's two-axis decomposition shows `result: likely_true` + `proof: unsound_but_recoverable`, say so plainly: *"The proof of Theorem 3 contains a load-bearing error, but the result itself is true via [alternative argument]. The author should rewrite the proof; no erratum is required for the claim."*
- The practical impact (safety, optimality, expository only, or proof-technique-only).
- If a counterexample exists, mention it here in one sentence.

If the safety impact is limited (e.g. the issue affects optimality but not safety, or affects only the proof technique while the result stands), state this explicitly. The reader should know in 30 seconds whether to panic.

### 3. Background (2–3 paragraphs)

Enough context for a reader unfamiliar with the specific paper. Define key notation. State the system model assumptions that are relevant to the finding. Cite the paper using `\cite{}` (LaTeX) or a linked reference (Markdown).

### 4. The Issue

Name this section to describe the specific flaw: *"The Gap"*, *"The Inversion"*, *"Non-Termination of the Iteration"*, or simply *"The Issue"*. 1–3 paragraphs.

Describe where in the proof the reasoning breaks down and why. Reference specific proof steps, equations, or lemmas from the paper. Be concrete: a reader should be able to put your brief next to the paper and follow along.

### 5. Counterexample (if available)

Present the counterexample using three subsections:

- **Instance.** Define the task set, system parameters, or graph structure. Use a `tabular`+`booktabs` table (LaTeX) or a Markdown table.
- **Trace.** Walk through the execution or computation step by step, showing how the claimed result fails.
- **Verification.** How was the counterexample verified? (Python script, exact computation, simulation, value iteration, exhaustive search.) Reference the script filename if applicable.

### 6. Adjudication (if stress-test data available)

Three paragraphs:

- **Strongest defense.** What's the best case for the paper? If the defense identified precondition violations or missing context (appendices, tech reports), present them. Be fair.
- **Verdict.** The stress-test arbiter's verdict (true_positive / likely_true_positive / inconclusive / etc.) and the key reasoning.
- **Flaw classification.** Flaw type, safety impact, quantitative severity, scope.

If the stress test was not run, omit this section.

### 7. Suggested Fix (1–2 paragraphs)

What change to the paper would resolve the issue? Be specific. Possibilities:

- Tighten the theorem statement by adding a precondition.
- Rewrite the proof to handle the missed case.
- Replace the result with a weaker but correct claim.
- Withdraw the result if no fix is possible.

State whether the fix preserves downstream results that depend on this one, or whether they also need to change.

### 8. References

The paper itself, any cited prior work invoked in the discussion, and any external material (appendices, tech reports) that were referenced.

## LaTeX preamble (when format = latex)

Start with:

```latex
\documentclass[11pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{hyperref}
\usepackage{booktabs}

\newtheorem{claim}{Claim}
\newtheorem{observation}{Observation}
```

Add `\usepackage{tikz}` + `\usetikzlibrary{arrows.meta}` *only* if a diagram genuinely clarifies the counterexample (e.g. a schedule visualization).

Output raw LaTeX. Do **not** wrap the output in Markdown code fences.

## Markdown formatting (when format = markdown)

Use standard CommonMark. Use `$...$` for inline math and `$$...$$` for display math (most Markdown renderers + the user's LaTeX tooling handle this). For tables, use Markdown's pipe-table syntax.

## Honesty discipline

- Lead with the strongest evidence first. Don't bury the counterexample under preamble.
- If the stress-test arbiter's verdict was `likely_false_positive` or `inconclusive`, **say so** in the overview. Don't write the brief as if the issue is confirmed when it isn't. The brief's job is to be a faithful record, not advocacy.
- Distinguish "I verified this" from "I have not yet verified this". If a defense argument cites an appendix you couldn't retrieve, note that explicitly: *"resolution depends on contents of Appendix A, not yet retrieved"*.
- Quantitative severity should be a *number* when possible. *"Bound is unsafe by approximately 0.05 in utilization"* is better than *"bound is unsafe"*.

## Output

A single document (LaTeX `.tex` source or Markdown `.md`), written to a file in the user's working directory if the tool supports file writes, or printed to the conversation otherwise. Filename suggestion: `finding-<result-label>.tex` or `finding-<result-label>.md`.
