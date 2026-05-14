# Case study: ILP schedulability analysis with a missing totality constraint

## Paper

S. Baruah, **Schedulability analysis using ILP**, *Proceedings of the 28th International Conference on Real-Time Networks and Systems (RTNS '20)*, ACM, 2020.

## Status of the issue

The ILP formulation as published in RTNS 2020 (Figure 3 of the paper) is missing a structural constraint that the encoding's correctness depends on. The follow-up at `papers/baruah/Submitted/2021-ILP-RTA.pdf` in the source corpus appears to be a revised formulation; a public errata or revised manuscript citation should be inserted here once available.

> **Note for contributors.** This example was selected for the gallery on the assumption that the issue has been publicly acknowledged via a followup paper or errata. If the maintainer cannot locate a public acknowledgement, the case should be moved out of the public gallery and into a private internal-validation corpus. See the [gallery's discretion note](../README.md#discretion-about-subjects).

## The flaw, briefly

The ILP encoding uses binary ordering variables `x_{ij}` to indicate whether job `i` is sequenced before job `j` on the same processor. The published formulation constrains `x_{ij} + x_{ji} ≤ 1` (at most one direction) but **does not constrain `x_{ij} + x_{ji} ≥ 1`** (totality of the ordering). Without the totality constraint, the ILP solver can assign `x_{ij} = x_{ji} = 0` — neither direction holds — which leaves the demand-bound constraints partially inactive and lets the solver declare *infeasible* problems *feasible*.

**Safety impact**: unsafe_bound. The published formulation can certify schedulability for task sets that are actually unschedulable.

**Severity**: moderate-to-serious. The discrepancy is small in absolute terms on minimal counterexamples (1 time unit of unaccounted demand on a 2-job instance with deadline 5 — a 20% relative error), but the failure is structural rather than edge-case: it triggers whenever the solver finds it advantageous to leave ordering variables unconstrained, which is in fact most non-trivial instances.

## What `audit-proof` catches

See [audit-excerpt.md](audit-excerpt.md) for a representative audit excerpt. The audit identifies the missing totality constraint as a **missing precondition** issue (Pattern family 3 in the [scheduling-theory domain pack](../../domain-packs/scheduling-theory.md)): a property the encoding's correctness relies on, but that the published formulation does not state.

Audit verdict: `likely_flawed`, with `Counterexample-falsifiable? yes` — i.e., a concrete task set can be constructed that exercises the gap. The two-axis decomposition gives `result_truth: likely_false` (the ILP's correctness claim is incorrect as stated) and `proof_soundness: unsound` (the soundness argument relies on totality without imposing it).

## What `find-counterexample` constructs

See [counterexample-excerpt.md](counterexample-excerpt.md) for the construction. The agent produces a 2-job instance with deadline 5 and total demand 6, then verifies independently (via direct simulation) that the task set is *unschedulable* while the published ILP declares it *schedulable*. The verification script is [verification-script.py](verification-script.py).

The counterexample is intentionally minimal: removing either job, or relaxing the deadline by one unit, eliminates the discrepancy. This is the "smallest violating instance" form that's most useful in a writeup.

## What `stress-test-defense` says

The defender (running in a fresh context) looks for legitimate counterarguments: maybe the missing constraint is implied by another constraint elsewhere in the formulation; maybe the paper's preamble pins `x_{ij}` to specific values; maybe a deferred companion technical report contains the missing constraint. None of these defenses hold for the published version — the constraint is genuinely absent. The arbiter then verifies the counterexample violates no precondition and renders `true_positive` with confidence `high`.

## What Proofreader recommends

For the published version: the formulation should add `x_{ij} + x_{ji} = 1` (totality of the ordering for every pair of jobs on the same processor). The fix is a one-line addition to the ILP encoding. After the fix, the 2-job counterexample no longer exhibits the discrepancy.

## Takeaways for plugin users

This case illustrates four specific Proofreader features doing their job:

1. **Cross-reference verification** flags that the published formulation's claim of "encoding faithfulness" cites no internal lemma that establishes totality — the chain of justification has a missing link.
2. **`scheduling-theory` domain pack** recognizes "ordering variables without totality" as a recognized failure mode (added to the pack's Pattern family 3 inventory after cases like this one).
3. **Two-axis decomposition** correctly classifies this as `result_truth: likely_false` (not just `proof_soundness: unsound`) — the published claim does not hold; the fix requires adding a constraint, not merely rewriting a proof.
4. **Counterexample agent** produces a minimal, reproducible artifact that an author or reviewer can verify in seconds, not minutes.

Run this case locally with the plugin installed:

```text
> Use evaluate-paper on papers/baruah-rtns-2020.pdf with domain=scheduling-theory.
> Now audit the ILP formulation (Figure 3) in adversarial mode.
> Run find-counterexample on the ILP formulation, targeting the
>   ordering-variable totality concern.
> /stress-test-defense ILP-Figure-3 mode=adversarial
```

Expected behavior: matches what's described above. (Exact wording will differ — model output is stochastic — but the verdict, severity classification, and counterexample structure should reproduce.)
