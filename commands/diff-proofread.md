---
description: Compare Proofreader audit outcomes between two versions of a paper. Shows what was fixed, what regressed, what's new, and what's unchanged -- useful for revision rounds, before/after responding to reviewers, or tracking convergence across drafts.
argument-hint: <old-paper.pdf-or-tex> <new-paper.pdf-or-tex> [mode=rigorous|adversarial] [domain=<pack>]
---

# /diff-proofread

Run an end-to-end audit comparison between two versions of a paper and produce a diff report. User argument: `$ARGUMENTS` — typically two paths to PDFs or `.tex` files. Parse optional `mode=`, `domain=`, and `format=` flags the same way `/proofread` does.

## Why this exists

Re-running `/proofread` from scratch on each revision wastes context, and worse, gives non-deterministic outputs that are hard to compare. Authors care about three specific questions during a revision round:

1. **Did I actually fix the issues from last time?** A `true_positive` from v1 should be missing in v2.
2. **Did I introduce any new issues?** New `likely_flawed` audits in v2 that weren't in v1.
3. **Are stable issues still stable?** Verdicts that didn't change between v1 and v2 — useful confidence signal.

`/diff-proofread` reuses prior audit/verdict artifacts where they exist, only re-runs stages for results that changed, and presents the deltas explicitly.

## Inputs

The command takes two paper paths. For each:
- A PDF, or
- A `.tex` file (or multi-file project root), or
- A path to an existing Proofreader report directory (e.g., `proofreader-report-v1/`).

If a Proofreader report directory is supplied, reuse the stored audits/verdicts directly. If a paper is supplied, run `/proofread` to produce a fresh report first.

## Steps

### 1. Establish both reports

If either input is a raw paper (not a report directory), invoke `/proofread` on it to produce a report. Use the same `mode` and `domain` for both sides — otherwise the diff is comparing apples to oranges.

Save the two reports as `proofreader-report-{old,new}.md` plus their per-finding briefs.

### 2. Match results across versions

Build a correspondence between formal results in v1 and v2. Match by:
- Identical label (Theorem 3 ↔ Theorem 3) — first pass.
- Semantic similarity for renamed/renumbered results (e.g., Theorem 3 in v1 became Theorem 5 in v2 after the author added two new theorems). Use the result statement's wording as the matching signal; ask the user to confirm matches that are ambiguous.

Some results in v2 will have no correspondent in v1 (newly added). Some in v1 will have no correspondent in v2 (removed). Both cases are important diff signals.

### 3. Classify each matched pair

For each matched pair, classify the verdict transition:

| v1 verdict | v2 verdict | Class | Implication |
|---|---|---|---|
| `flawed` / `likely_flawed` | `correct` / `likely_correct` | **Fixed** | The author successfully resolved this. |
| `flawed` / `likely_flawed` | `uncertain` | **Partially fixed** | Severity reduced; some concerns remain. |
| `correct` / `likely_correct` | `flawed` / `likely_flawed` | **Regression** | A change introduced a new issue. Highest-priority finding for the author. |
| `correct` | `correct` | **Stable** | No diff. |
| `flawed` | `flawed` | **Unfixed** | Same issue persists; the revision did not address this finding. |
| (no v1 entry) | any | **New result** | This theorem/lemma is new in v2. Treat verdicts at face value. |
| any | (no v2 entry) | **Removed result** | The author dropped this result. Verify intentional, not an editing accident. |

For the two-axis decomposition introduced in [audit-proof](../skills/audit-proof/SKILL.md), also diff `result_truth` and `proof_soundness` independently. A common revision pattern is *result_truth stays `true`, proof_soundness goes from `unsound` to `sound`* — the author rewrote the proof. Surface this explicitly.

### 4. Diff the issues within each pair

For pairs that remain `likely_flawed` or `flawed` in both versions, drill in: are the *issues* the same (just unfixed) or *different* (one issue fixed but a new one introduced in the same proof)? Match issues by location + type.

### 5. Produce the diff report

```markdown
# Proofreader Diff: <paper title> v1 → v2

**v1**: <path or report dir>
**v2**: <path or report dir>
**Mode**: <mode>
**Date**: <ISO>

## Headline

- **Fixed**: N
- **Regressed**: M
- **Unfixed**: K
- **New issues**: J
- **Removed results**: L

If M > 0, **start the review here** — regressions are the highest-priority signal.

## Regressions (highest priority)

For each regression:
- **<Result label>**: v1 verdict → v2 verdict. What changed in the proof. Likely cause.

## Fixed

For each fix:
- **<Result label>**: v1 verdict → v2 verdict. Brief note on what the author appears to have changed (proof rewrite, added precondition, removed claim, etc.).

## Unfixed (carried over)

For each:
- **<Result label>**: still flagged. Either the author hasn't addressed it or the fix didn't take. Reference the v1 finding brief.

## Two-axis decomposition transitions

Notable changes in `(result_truth, proof_soundness)`:

- **<Result label>**: (likely_true, unsound) → (likely_true, sound) — proof rewrite resolved the soundness issue without touching the claim.

## New results in v2

- **<Result label>**: v2 verdict. (No v1 baseline.)

## Removed results

- **<Result label>**: was in v1, gone in v2. Verify intentional.

## Stable results (no change)

Bulleted list. These didn't change between versions — confidence signal that the audits are stable.
```

### 6. Recommended next steps

Always end with concrete actions:

- Regressions → re-audit the modified proof; consider reverting the change that introduced the regression.
- Unfixed → consult the v1 finding brief for guidance; the issue is real and persistent.
- New issues → run `/stress-test-defense` to confirm before treating as authoritative.

## Caching and incremental computation

When v1 was produced by an earlier `/proofread` run that stored audits per result, the diff can avoid re-auditing results whose proof text is unchanged (compare extracted proof text byte-for-byte; if identical, copy the v1 audit forward). This is most useful when v2 is a small revision of v1.

If v1's report doesn't exist (only the PDF was kept), full re-run is required. Suggest to the user that future revisions should preserve the report directory to enable cheap diffs.

## Limitations

- Result-matching is heuristic. For renamed theorems, the matcher may need user input.
- The two paper versions must use the same domain pack(s) — otherwise the audits aren't comparable.
- Stochastic LLM output means rerunning `/proofread` on the same paper twice can produce slightly different audits. The diff is meaningful for *substantive* deltas (verdict changes, new/removed issues), not for cosmetic differences in audit prose.
