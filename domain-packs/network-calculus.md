---
name: network-calculus
applies_to: Deterministic network calculus, (min,+) and (max,+) algebra, arrival / service / departure curves, real-time networking.
detection_hints:
  - References (min,+) algebra, arrival curves, service curves, departure curves
  - Uses ⊗ (min-plus convolution), ⊘ (deconvolution), ⊕ (min-plus addition / min)
  - Cites Le Boudec, Thiran, Cruz, Chang, Bouillard
  - Defines latency-rate servers, leaky-bucket arrival curves, token buckets, GCRA
---

# Domain pack: Network calculus (starter)

**Status**: starter pack. Community contributions welcome — see [domain-packs/README.md](README.md). Patterns below are based on the more common flaw families in this subfield; specificity will grow as the pack matures.

## When this pack applies

Papers whose central claims are end-to-end latency bounds, backlog bounds, or arrival-curve transformations in the deterministic network-calculus framework. Includes real-time networking (TSN, AVB, deterministic Ethernet), arbitration analysis (TDMA, FIFO, priority queueing on shared links), and any analysis built on `(min,+)` algebra.

## Common flaws in this subfield

### Pattern 1 — Direction of deconvolution
- **Mechanism**: `(min,+)` deconvolution `α ⊘ β` is not commutative and not associative the way ordinary algebra is. Proofs sometimes apply identities valid for ordinary algebra (`(α ⊘ β) ⊘ γ = α ⊘ (β ⊗ γ)`) in the wrong direction or under conditions where they don't hold.
- **What to check**: every `⊘` step — confirm both operand types (curve vs. function) and the identity being invoked. Re-derive using Le Boudec & Thiran's identity tables.
- **Counterexample-falsifiable?** yes — small piecewise-linear curves where the wrong-direction identity gives a different value.

### Pattern 2 — Sub-additive closure assumed without proof
- **Mechanism**: `(min,+)` convolution of an arrival curve with itself is sub-additive only under specific conditions. Proofs sometimes assume `α ⊗ α = α` (idempotency) for curves that aren't actually sub-additive.
- **What to check**: when the proof uses `α* = α ⊗ α ⊗ …`, confirm the curve is sub-additive (or that the sub-additive closure operation `α*` is being applied correctly).
- **Counterexample-falsifiable?** yes — curves with concave segments that violate sub-additivity.

### Pattern 3 — Backlog vs. delay duality
- **Mechanism**: confusing horizontal deviation (delay bound) with vertical deviation (backlog bound). The two are related but not equal — a delay bound times the arrival rate is *not* always the backlog bound, especially for non-affine curves.
- **What to check**: when the proof derives a delay bound from a backlog bound or vice versa, the conversion must use the specific deviation formula, not a heuristic multiplication.
- **Counterexample-falsifiable?** yes — piecewise-linear arrival/service curves where the two bounds diverge.

### Pattern 4 — Service curve type confusion
- **Mechanism**: "simple", "strict", and "weakly-strict" service curves have different properties. Proofs sometimes invoke an identity (e.g., the concatenation theorem) under the wrong type. Latency-rate servers behave differently than general service curves.
- **What to check**: every service-curve invocation — confirm the type and that the identity used is valid for that type.
- **Counterexample-falsifiable?** yes — flows where a simple service curve gives a different bound than a strict service curve.

### Pattern 5 — Pay-multiplexing-only-once misapplied
- **Mechanism**: the PMOO principle improves bounds by accounting for multiplexing once across a path. Proofs sometimes apply it on paths where the flows don't actually share the multiplexing point claimed, leading to optimistic bounds.
- **What to check**: verify the topology — do all the flows the proof groups under PMOO actually share the same multiplexing arbiter at the claimed node?
- **Counterexample-falsifiable?** yes — multi-hop topologies where the proof's flow-grouping assumes shared arbitration that doesn't exist.

## Standard results commonly invoked in this subfield

- **Le Boudec & Thiran** identity tables for `(min,+)` and `(max,+)` algebra.
- **Cruz's network-calculus framework** — original arrival/service curve definitions and the three basic theorems (output bound, delay bound, backlog bound).
- **Concatenation theorem** — for a tandem of service curves, the end-to-end service curve is the `(min,+)` convolution.
- **Pay-bursts-only-once / Pay-multiplexing-only-once** — bound-improvement techniques for tandem networks.
- **Chang's stochastic network calculus** (when probabilistic).
- **Total Flow Analysis (TFA)** and **Separated Flow Analysis (SFA)** — bound computation methods.

## Counterexample attack surfaces

- **Single-kink piecewise-linear curves** — minimal arrival/service curves that exhibit a sub-additivity or convexity issue, often with one slope change at the boundary parameter.
- **Two-flow tandem with reverse priority** — networks where flow priority order changes between two hops; exposes PMOO misapplications.
- **Burst-only and rate-only limits** — set arrival curve to pure burst (`α(t) = b` for `t > 0`) or pure rate (`α(t) = rt`) to expose limits-of-form bugs.
- **Backpressure / blocking** — flows whose service curve drops to zero for an interval, exposing assumed continuity.
- **Cyclic topologies** — many tools and proofs assume DAGs; cycles expose hidden assumptions.
- **Per-flow-vs-aggregate** — single-flow bounds applied to aggregates (or vice versa) when the curves don't decompose the way assumed.
