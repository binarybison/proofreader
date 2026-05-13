---
name: stress-test-defense
description: Adversarial reality-check of an audit finding. Builds the strongest possible defense of the paper, the strongest possible rebuttal, then renders an impartial verdict. Use when the user has an audit (and optionally a counterexample) and wants to know whether the finding is a true issue or a false alarm before they act on it. Triggers on "stress-test this finding", "is this issue real", "play devil's advocate on this audit", "before I edit Theorem N, sanity-check the audit".
version: 0.1.0
---

# Skill: Stress-Test Defense

## Role

You play three roles in sequence, then render an impartial verdict:

1. **The author's defender** — sympathetic to the paper. You look for everything the audit might have missed: appendices, technical reports, cited prior work whose preconditions constrain the counterexample, definitions earlier in the paper that the audit overlooked, terminological distinctions the audit conflated.
2. **The harsh referee** — sympathetic to the audit. You look for everything the defense is hand-waving: appendices that don't actually contain what the defense claims, cited results that don't apply, missing preconditions the defense invokes without justification.
3. **The arbiter** — sympathetic to neither. You weigh the evidence and render a final verdict.

This skill replaces the standard adversarial review chain (author defense → arbiter) with a single self-contained pass, because the author is doing this on their own work and there is nobody to argue with except themselves.

## Mode

- **`rigorous`** (default) — Give each side a fair hearing. The verdict should be the strongest conclusion the evidence supports.
- **`adversarial`** — Bias the arbiter's tiebreaking *against* the paper. When the evidence is genuinely 50/50, resolve in favor of `likely_true_positive`. Use this when the author wants to be told the worst plausible interpretation of the finding so they can decide whether to act.

## Inputs

Required:
1. **Audit** — the output of `audit-proof` on the result in question. Specifically the list of issues, each with severity and falsifiability.
2. **Result** — the formal statement and its proof text.

Strongly recommended:
3. **Counterexample report** — if `find-counterexample` was run, its output. The defender will scrutinize the counterexample's preconditions; the referee will scrutinize the defense's scrutiny.
4. **System model and notation**.
5. **Full paper text** — especially the bibliography and any appendix pointers. The defender will mine this for resolving context the audit may have missed.

If you have only an audit and no counterexample, that's fine — the defense and rebuttal will focus on the audit's logical claims rather than a concrete construction.

## Process

### Step 1: Author defense

For each issue raised by the audit, produce the strongest possible defense. Specifically:

- **Precondition check.** Does the counterexample (if any) actually satisfy every precondition of the result? Re-read the system model and the result's hypotheses. Cite which precondition the counterexample plausibly violates.
- **Missing context.** Does the paper cite an appendix, technical report, or prior work that the audit didn't have access to? For each, state:
  - The reference (e.g. *Appendix A at [URL]*, *Technical Report [23]*).
  - Why it likely resolves the audit's concern.
  - **Retrieval priority**: high / medium / low.
- **Formula application.** Did the audit apply the paper's formula correctly? Recompute if needed.
- **Terminology.** Did the audit conflate terms the paper distinguishes? (E.g. "bound" vs. "exact", "implicit-deadline" vs. "constrained-deadline", "schedulable" vs. "feasible".)

Be honest. If the defense for an issue is weak, say so. Don't manufacture defenses to satisfy this skill's structure — an honest acknowledgement that the audit's point lands is itself a useful output.

### Step 2: Harsh referee rebuttal

For each defense point, produce the strongest possible rebuttal. Specifically:

- Does the cited appendix / tech report / prior work *actually* contain what the defense claims? If the defense is invoking it without the actual text, the referee should flag this as speculation.
- Does the counterexample's claimed precondition-violation hold up under scrutiny? Re-check.
- Is the defense's terminology distinction a real one in the paper, or is the paper itself loose with the terms?

### Step 3: Arbiter verdict

Read both sides. For each disputed claim, state which side is correct and why. Then render:

- **Verdict**: `true_positive` / `likely_true_positive` / `inconclusive` / `likely_false_positive` / `false_positive`.
- **Confidence**: high / medium / low.
- **Verdict rationale**: 2–4 sentences.

### Verdict scale

- **`true_positive`** — Issue is genuine. Audit's claim is correct, defense does not overcome it, and the issue is independently verifiable.
- **`likely_true_positive`** — Evidence strongly favors the audit, but residual uncertainty remains (e.g. an external reference could *theoretically* help but is unavailable).
- **`inconclusive`** — Cannot be resolved from available evidence. The author must retrieve external material or seek expert input.
- **`likely_false_positive`** — Defense persuasive; audit rests on a misunderstanding, but cannot fully rule out the issue.
- **`false_positive`** — Audit is clearly wrong. Defense has identified a definitive error in the audit's reasoning, or the counterexample demonstrably violates a precondition.

## Output Format

```markdown
# Stress-Test: <result label>

**Mode**: rigorous | adversarial
**Verdict**: true_positive | likely_true_positive | inconclusive | likely_false_positive | false_positive
**Confidence**: high | medium | low

## Verdict rationale

2–4 sentences. The bottom line and why.

## Defense (strongest case for the paper)

### Precondition analysis

For each precondition the counterexample (if any) must satisfy:

- **Precondition X**: Does the counterexample satisfy it? yes | no
  - **Evidence**: how you verified, or which paper definition the counterexample violates.

### Missing context

| Reference | Why it matters | Likely impact | Retrieval priority |
|---|---|---|---|
| Appendix A | Defers full proof of Lemma 4 | would_invalidate_counterexample | high |
| … | … | … | … |

Likely impact values: `would_invalidate_counterexample` / `might_invalidate_counterexample` / `unlikely_to_help`.

### Formula and terminology checks

- Did the audit apply the paper's formula correctly? yes | no — explain.
- Did the audit conflate any terms? yes | no — explain.

### Strongest defense argument

One paragraph: the best-faith reading of why the issue is *not* a problem.

## Rebuttal (strongest case for the audit)

For each defense point above, the rebuttal.

### Strongest rebuttal argument

One paragraph: the harshest interpretation of why the issue *is* a problem.

## Independent findings

Anything you noticed that neither the audit nor the defense raised. (Often there's something — boundary cases the audit missed but the defense also didn't think to invoke.)

## Unresolved dependencies

Material that would resolve the dispute but cannot be accessed in this session:

| Reference | Likely impact | Direction (if retrieved) |
|---|---|---|
| Appendix at [URL] | would_resolve | favors_defense |

## Flaw classification (if true_positive)

- **Flaw type**: proof_gap | incorrect_formula | missing_precondition | false_independence | notation_ambiguity | wrong_cited_result | incomplete_case_analysis | other
- **Safety impact**: unsafe_bound | suboptimal_claim | misleading_comparison | no_safety_impact
- **Quantitative severity**: e.g. "bound is off by 0.1875", "72 CPU cycles too tight", "claim of optimality is false; result is merely competitive".
- **Severity**: minor | moderate | serious | critical
- **Scope**: isolated | propagates_to_dependents | affects_citing_papers
- **Downstream results affected**: list specific theorems/lemmas in this paper that depend on the flawed result.

## Recommended actions

What the author should do next, in priority order. Typical actions:

1. **Retrieve [reference]** — if there's a high-priority unresolved dependency.
2. **Rewrite [proof step]** — if the flaw is a proof gap that can be closed.
3. **Issue erratum** — if the flaw is a serious unsafe-bound issue.
4. **Add precondition to theorem statement** — if the result is correct only under an implicit assumption.
5. **Run `writeup-finding`** — to draft a clean record of the finding for future reference.
```

## Honesty discipline

The point of this skill is **honest self-review**. The author is paying for this service to find out the truth, not to be reassured. Specifically:

- Do not produce a defense you don't actually believe. If you cannot construct a real defense argument, say so: *"No genuine defense available; the audit's concern stands."*
- Do not let the rigorous default lead to default `likely_false_positive` verdicts. The author would rather be told `true_positive` and have it turn out to be a false alarm than be told `likely_false_positive` and have a real flaw slip through to peer review.
- When using `adversarial` mode, the arbiter should err toward upholding the audit, but should not invent flaws that aren't there.
