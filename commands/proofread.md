---
description: End-to-end rt-proofreader pass on a paper. Evaluates, audits flagged proofs, hunts counterexamples, stress-tests findings, and writes them up.
argument-hint: <paper.pdf> [mode=rigorous|adversarial]
---

# /proofread

Run the full rt-proofreader pipeline on a single paper. The user's argument is `$ARGUMENTS` (typically a path to a PDF or a paper title). If the argument includes `mode=adversarial`, use adversarial mode throughout; otherwise default to `rigorous`.

## Pipeline

Execute these in order, and only proceed to the next stage if the previous stage produced material for it to operate on:

1. **`evaluate-paper`** on `$ARGUMENTS`.
   - Output: the per-result list with verdicts.
   - Identify the set of *flagged* results: those whose verdict is worse than `correct` (i.e. `likely_correct`, `uncertain`, `likely_flawed`, or `flawed`).

2. **`audit-proof`** on each flagged result.
   - For each, produce the audit report. Identify which audits have at least one issue with `severity ≥ moderate` and `Counterexample-falsifiable? yes`.

3. **`find-counterexample`** on each result whose audit landed at `likely_flawed` or `flawed`.
   - For results with `likely_flawed` but no falsifiable issues, skip this stage and note in the final report that the issue is expository.

4. **`stress-test-defense`** on each result with a constructed counterexample, *and* on each `likely_flawed` audit even if no counterexample was found.
   - Skip purely-expository `uncertain` audits.

5. **`writeup-finding`** on each result the stress-test confirmed as `true_positive` or `likely_true_positive`.
   - Default to Markdown for the orchestrator (LaTeX briefs are usually written up later, manually). Override with `format=latex` in the argument list.

## Final report

After all stages, assemble a top-level `proofreader-report.md` in the user's working directory with this structure:

```markdown
# Proofreader Report: <paper title>

**Mode**: rigorous | adversarial
**Date**: <ISO date>

## Summary

- Paper scores: …
- Formal results: <N total>, <K flagged>, <C confirmed flaws>

## Confirmed findings

For each `true_positive` / `likely_true_positive`:
- **<Result label>**: 1-line description. → `finding-<label>.md`

## Open questions

For each `inconclusive` stress-test verdict:
- **<Result label>**: what evidence would resolve it.

## Dismissed concerns

For each `likely_false_positive` / `false_positive`:
- **<Result label>**: brief reason the audit's concern did not hold up. Useful so the author doesn't accidentally re-flag this later.

## Audits without falsifiable concerns (proof-style issues)

For each result flagged in evaluate-paper but where the audit found only proof-style/expository issues:
- **<Result label>**: list the suggested proof-rewrites.
```

## Communication during the run

- Announce each stage before you begin it ("Stage 2/5: auditing 4 flagged proofs"). Keep updates terse.
- If a stage produces zero candidates for the next stage, skip the next stage and say so.
- If the user's tool environment cannot execute Python, the `find-counterexample` stage will produce verifiable scripts rather than verified counterexamples — note this in the final report.

## Cost discipline

A full run on a moderately complex paper can consume substantial tokens (each audit, CX hunt, and stress-test is its own long-context call). Before launching, give the user a 1-line plan:

> *"Plan: evaluate the paper, audit ~5 likely-flagged proofs, hunt counterexamples on ~2, stress-test, write up. Estimated 30–60 minutes wall time, 100k–500k tokens depending on paper length and difficulty. Proceed?"*

…then wait for confirmation unless the user invoked `/proofread` with an explicit `confirm` argument.
