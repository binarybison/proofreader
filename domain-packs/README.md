# Domain packs

Proofreader's built-in flaw patterns are intentionally biased toward classical real-time scheduling. **Domain packs** extend that coverage to adjacent subfields where the recurring flaw modes are different: network calculus, control-theoretic bounds, probabilistic real-time, distributed real-time, hardware-shared-resource analysis, mixed-criticality systems, DAG / parallel-task scheduling, and so on.

A domain pack is one Markdown file that the audit skills load alongside the core prompt. Each pack provides:

1. **A short subfield description** — what kinds of papers this pack applies to, and how to detect that a paper falls in this subfield (so the audit can auto-select packs).
2. **Common recurring flaw mechanisms** — specific to the subfield, observed in published papers, with the kind of concreteness that helps the model recognize the pattern.
3. **Domain-specific standard results** — the "you don't have to restate this" inventory for the defender, so the audit doesn't flag invocations of well-known prior work as proof gaps. (E.g., for network calculus: the sub-additive closure of `(min,+)`, deconvolution direction; for control: Lyapunov stability.)
4. **Domain-specific counterexample attack surfaces** — the kinds of degenerate / boundary inputs that have produced counterexamples in this subfield (e.g., for `(min,+)` arrival curves: piecewise-linear with a single kink at the boundary; for control: marginal-stability eigenvalues).

## How to use a domain pack

Cite the relevant pack(s) in your invocation:

```text
> Audit Theorem 5 of my-paper.pdf using domain pack network-calculus.
```

…or, when running `/proofread`:

```text
> /proofread my-paper.pdf domain=network-calculus
```

You can stack multiple packs (e.g., `domain=scheduling-theory,probabilistic`) for papers that span subfields. The audit skill loads each pack's patterns and treats them additively — generic patterns from the core prompt still apply.

## Available packs

| Pack | Status | Scope |
|---|---|---|
| [`scheduling-theory`](scheduling-theory.md) | Baseline — patterns originally distilled from the source corpus | Uniprocessor and multiprocessor scheduling, response-time analysis, fixed-priority and EDF, mixed-criticality |
| [`network-calculus`](network-calculus.md) | Starter (community contributions welcome) | Deterministic network calculus, `(min,+)` algebra, arrival / service curves |
| `control-theoretic-bounds` | Planned | Stability, optimality, robustness in real-time control loops |
| `probabilistic-rt` | Planned | pWCET, probabilistic response time, MBPTA |
| `distributed-rt` | Planned | Distributed scheduling, time synchronization, consensus latency |
| `dag-parallel` | Planned | Federated / global scheduling of parallel tasks, work-stealing analyses |
| `shared-resources` | Planned | Cache analysis, DRAM, NoC, GPU contention, semaphore-based protocols |

## Contributing a pack

Two paths.

### Hand-written (recommended for first cut)

1. Read [`scheduling-theory.md`](scheduling-theory.md) as a template — copy its structure.
2. Pick a subfield you know well. Write one section per recurring flaw mechanism. **Specificity beats coverage.** A pack with three razor-sharp patterns is more useful than one with ten generic ones.
3. List the subfield's standard results — the ones a reviewer would know and not require restatement. This directly reduces false-positive proof_gap flags in your subfield.
4. List 2–4 attack-surface patterns for counterexample search — the "degenerate inputs that have actually broken proofs in this area" inventory.
5. Submit a PR. Include 1–2 anonymized examples (paper + result label + audit output) if you have them — they validate the patterns are real.

### Mechanically generated with Claude

If you have a corpus of confirmed flaws in your subfield (analogous to the source corpus that produced `scheduling-theory.md`):

1. Tag each confirmed flaw with a domain label and a mechanism description.
2. Cluster mechanisms by family — Claude can help with the clustering pass.
3. Have Claude draft the pack in the same structure as [`scheduling-theory.md`](scheduling-theory.md), grounding each mechanism in concrete example sentences from the flaw notes.
4. Hand-edit the result for accuracy and tone. Mechanical drafts tend to overgeneralize; the maintainer's job is to keep specificity high.

The repo's [examples](../examples/) directory has worked instances of the patterns in action.

## Pack file format

```markdown
---
name: <pack-name>
applies_to: short one-line description of which papers this targets
detection_hints: bulleted list of keywords / paper-type signals that suggest this pack is relevant
---

# <Pack name>

## When this pack applies

2–3 sentences describing the subfield's scope and boundaries.

## Common flaws in this subfield

### Pattern 1 — <Short title>
- **Mechanism**: how this flaw typically manifests, in 1–3 sentences.
- **What to check**: concrete questions the auditor should ask.
- **Counterexample-falsifiable?** yes / no, with reasoning.

(Repeat for 3–8 patterns. Quality > quantity.)

## Standard results commonly invoked in this subfield

A bulleted list. For each: the standard result's name + a one-line scope ("Liu-Layland — EDF optimality on uniprocessor implicit-deadline").

## Counterexample attack surfaces

A bulleted list of subfield-specific degenerate / boundary inputs that have been productive in past counterexample searches.
```

Keep packs to roughly 1500 words or fewer — they need to fit comfortably into the audit's context budget alongside the paper text.
