---
name: scheduling-theory
applies_to: Real-time scheduling theory and response-time analysis papers (uniprocessor and multiprocessor; fixed-priority and EDF; mixed-criticality; arbitrary-deadline variants).
detection_hints:
  - Discusses task models with parameters (C, T, D), jobs, releases, deadlines
  - References EDF, RM, DM, fixed-priority, global / partitioned / semi-partitioned scheduling
  - Proves schedulability tests, response-time bounds, demand-bound / supply-bound functions
  - Cites Liu-Layland, Dertouzos, Baruah, Bertogna, Audsley, Davis-Burns
---

# Domain pack: Scheduling theory (baseline)

## When this pack applies

This is Proofreader's default pack. It targets papers whose central contribution is a schedulability test, response-time bound, optimality result, or speedup factor for a real-time task model. It does *not* specialize to network calculus, control loops, probabilistic timing, hardware contention, or DAG-parallel models — separate packs cover those.

## Common flaws in this subfield

### Pattern 1 — Incorrect formulas
- **Mechanism**: sign / condition inversions; wrong-direction `R⁻`/`R⁺` substitution in induction; dropped jitter, blocking, or context-switch terms across an algebraic step; wrong floor/ceiling direction; constants assumed equal to 1 when paper's own data shows variability; one-sided pruning rules; wrong denominator with no counting justification.
- **What to check**: re-derive each algebraic step independently. Count terms across the simplification — fewer terms after must be justified.
- **Counterexample-falsifiable?** yes — if the formula governs a schedulability decision or numerical bound.

### Pattern 2 — Missing preconditions hidden in informal language
- **Mechanism**: theorem says "backlogged", proof requires "continuously backlogged"; lemma's monotonicity described as "ideal" rather than "assumed"; structural facts ("at most one shared switch") treated as observations when they're actually preconditions; FIFO ordering, work-conservation, homogeneity invoked but not stated.
- **What to check**: extract every condition the proof relies on. Each must appear in the theorem statement or in an explicit precondition list.
- **Counterexample-falsifiable?** yes — construct an instance that violates the unstated precondition while satisfying every stated one.

### Pattern 3 — False independence in coupled structures
- **Mechanism**: split sub-jobs treated as independent sporadic jobs; reconvergent DAG paths treated as independent; multiple maxima taken independently over a coupled set.
- **What to check**: any time the proof says "by independence of …" or applies an inequality for independent random variables / tasks, verify that independence formally holds, not just that the components look separate.
- **Counterexample-falsifiable?** yes — exhibit two coupled components whose joint extremum exceeds the sum / max the proof bounds them by.

### Pattern 4 — Incomplete case analysis
- **Mechanism**: read case treated, write case not (or vice versa); single-event handling when batch effects matter; context-switch preemption analyzed, interrupt preemption omitted; boundary states (queue overflow, hyperperiod release, first job) skipped.
- **What to check**: list every case the proof's logic implicitly partitions over (read/write, preempt-by-interrupt/by-context-switch, queue full/not-full, first/subsequent job). Each must be handled.
- **Counterexample-falsifiable?** yes — feed an instance that exercises the omitted case.

### Pattern 5 — Cross-reference misapplication
- **Mechanism**: invoking Lemma N from this paper or a prior paper when its preconditions don't hold; using a `≤` bound as `=`; applying a result proven for implicit-deadline tasks to a constrained-deadline task set.
- **What to check**: every "by Lemma X" / "applying Theorem Y" — re-read the cited statement, verify preconditions, verify direction-of-use.
- **Counterexample-falsifiable?** sometimes — a task set that satisfies the citing paper's model but violates the cited lemma's preconditions.

### Pattern 6 — Quantifier and notation issues that matter
- **Mechanism**: off-by-one quantifier range (`∀l > 1` vs `∀l > 0`); "almost surely" in proof but not in theorem statement; prose definition wider than the equation captures.
- **What to check**: test the boundary value of every universal quantifier in the theorem statement. Re-read probabilistic claims for matching quantifier strength between proof and statement.
- **Counterexample-falsifiable?** yes for off-by-one; partial for prose/equation mismatches.

## Standard results commonly invoked in this subfield

When the audit complains that one of these is "unjustified" or "not proved", the audit is wrong — the result is well-known and expected to be invoked without restatement.

- **Liu-Layland** (1973): RM optimality among fixed-priority schedulers on uniprocessor implicit-deadline; utilization bound `n(2^(1/n) − 1)`.
- **Dertouzos** (1974): EDF optimality among preemptive uniprocessor schedulers; utilization bound 1 for implicit-deadline.
- **Audsley's recurrence**: response-time analysis for fixed-priority on uniprocessor with arbitrary deadlines.
- **Baruah** demand-bound function (DBF) and supply-bound function (SBF) calculus.
- **Bertogna's interference bound** for global fixed-priority multiprocessor scheduling.
- **Davis-Burns response-time recurrence** for global FP-MP.
- **Chetto / Silly-Chetto** processor-demand inequalities for EDF schedulability.
- **McNaughton's wrap-around rule** for preemptive scheduling on parallel machines.
- **Mok-Dertouzos** / **Spuri** equivalence between processor-demand and schedulability under EDF.
- **OPA** (Optimal Priority Assignment) — Audsley's algorithm.

## Counterexample attack surfaces

Productive degenerate / boundary inputs for scheduling-theory counterexample searches:

- **Hyperperiod-boundary releases** — jobs released exactly at `LCM(T_i)`, where the analysis's window boundary becomes ambiguous.
- **Two-task sets with one tight deadline** — minimal configurations where one task's blocking exactly equals another's slack.
- **Utilization at exactly 1.0** — the edge case for EDF schedulability that breaks many non-tight bounds.
- **Single-processor degeneracy** — multiprocessor analyses applied to `m = 1` often expose hidden division-by-`(m−1)` issues.
- **Zero-cost / zero-period limits** — `C_i → 0` or `T_i → 0` to expose limits-of-form bugs.
- **Implicit-deadline only** — feed `D_i = T_i` instances to constrained-deadline analyses; many bounds collapse incorrectly.
- **First-job-only releases** — task sets where only one job of each task is released, exposing first-iteration assumptions in iterative response-time recurrences.
- **Carry-in / carry-out skew** — adversarially chosen phase offsets so carry-in jobs from higher-priority tasks straddle the analysis interval.
