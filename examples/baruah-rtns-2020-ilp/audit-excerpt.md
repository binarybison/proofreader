# Audit: ILP Formulation (Figure 3)

**Mode**: adversarial
**Domain pack**: scheduling-theory
**Verdict**: likely_flawed
**Confidence**: high

**Result truth**: likely_false
**Proof soundness**: unsound
**Soundness-pattern tag**: none — this is a result-falsity issue, not a "proof-only" issue
**Alternative argument**: not applicable; the published formulation's correctness claim does not hold.

## Summary

The ILP encoding's correctness relies on the ordering variables `x_{ij}` (for pairs of jobs sharing a processor) satisfying a *totality* property: for every pair `(i, j)` on the same processor, exactly one of `x_{ij}` or `x_{ji}` is 1. The published formulation enforces only the *anti-symmetry* half (`x_{ij} + x_{ji} ≤ 1`); it omits the totality half (`x_{ij} + x_{ji} ≥ 1`). The omission lets the solver leave both `x_{ij}` and `x_{ji}` set to 0, which structurally disables the demand-bound constraints for the affected pair and causes the encoding to certify infeasible instances as feasible.

## Issues

### Issue 1: Missing totality constraint on ordering variables

- **Type**: missing_precondition
- **Severity**: serious
- **Location**: Figure 3, the constraint block for ordering variables `x_{ij}` (no equation number in the published version).
- **Description**: The encoding assumes that, for every pair of jobs `(i, j)` co-located on the same processor, the variables `x_{ij}` and `x_{ji}` form a binary partition: exactly one of them is 1. The published constraints enforce anti-symmetry (at most one is 1) but not totality (at least one is 1). The intended semantics of the demand-bound block depend on totality.
- **Why it matters**: when totality fails, the demand-bound constraints for the affected pair become vacuous. The solver can assign workload to a processor without ever activating the per-pair demand contribution. This means task sets that are actually unschedulable can be reported as schedulable. Safety classification: `unsafe_bound`.
- **Suggested fix**: add `x_{ij} + x_{ji} = 1` for every pair `(i, j)` co-located on the same processor. This is a one-line addition that preserves the rest of the formulation.
- **Counterexample-falsifiable?**: yes. A 2-job instance with total demand 6 and deadline 5 exercises the failure mode.

### Issue 2: Demand-bound aggregation depends on Issue 1

- **Type**: dependency_error
- **Severity**: moderate
- **Location**: the demand-bound aggregation block following the ordering definitions.
- **Description**: The aggregation uses `c_{ijk}` terms whose intended meaning is "demand contributed by job `j` to interval `k` when sequenced after job `i`". This meaning is only well-defined when the ordering is total. With Issue 1 unfixed, `c_{ijk}` for pairs with neither direction asserted is left unconstrained, which propagates to the aggregate.
- **Why it matters**: this is the mechanism by which the encoding-level issue (Issue 1) becomes an instance-level safety issue. Without it, Issue 1 would be a cosmetic gap. With it, Issue 1 is a soundness flaw.
- **Suggested fix**: fixed automatically once Issue 1 is fixed; no separate change required.
- **Counterexample-falsifiable?**: yes — same counterexample as Issue 1.

## Positively verified

- The remainder of the encoding (job-release timing, deadline-bound aggregation across intervals, processor-capacity constraints) is consistent and correctly enforces the intended semantics under the assumption that the ordering is total. The bug is localized to the ordering block.
- The paper's overall narrative — ILP as a tool for verifying schedulability of complex task sets — is sound; only the specific encoding has the gap.
- No issues with the proof of the embedding's soundness *given* totality. The published proof would go through unchanged if totality were imposed.

## Recommended next step

- Run `find-counterexample` to confirm the 2-job instance described. ✓ (See [counterexample-excerpt.md](counterexample-excerpt.md).)
- Then run `/stress-test-defense ILP-Figure-3` to confirm the missing constraint is not implied by some other constraint elsewhere in the formulation that the audit may have missed.
- If the stress-test confirms `true_positive`: run `writeup-finding` in `latex` format and propose the one-line fix as an erratum patch.
