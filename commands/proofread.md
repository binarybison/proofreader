---
description: End-to-end Proofreader pass on a paper. Evaluates, audits flagged proofs (one per result), hunts counterexamples in fresh subagents, stress-tests findings via fresh defender + arbiter subagents, and writes the results into a structured report directory.
argument-hint: <paper.pdf> [mode=rigorous|adversarial] [format=markdown|latex] [out=<dir>]
---

# /proofread

Run the full Proofreader pipeline on a single paper. User argument: `$ARGUMENTS` (typically a path to a PDF or a paper title). Parse out optional `mode=adversarial` (default `rigorous`), `format=latex` (default `markdown` for writeup-finding outputs), and `out=<dir>` (default `proofreader-report/` in the user's working directory).

## Pipeline structure

| Stage | Form | Granularity | Why |
|---|---|---|---|
| 1. evaluate-paper | inline skill | 1× per paper | Breadth-first inventory of every formal result. Shared context with the orchestrator. |
| 2. audit-proof | inline skill | **1× per flagged result** | Deep audit; mirrors the original pipeline's per-result invocation. Stays in main context so the user can follow along. |
| 3. find-counterexample | **subagent** | 1× per likely-flawed audit | Long, agentic, Python-heavy. Isolated to keep its noise out of main context. |
| 4. stress-test-defense | **two subagents** | 1× per result with CX or `likely_flawed`+ audit | Defender and arbiter each run in fresh isolated contexts for genuine independence. |
| 5. writeup-finding | inline skill | 1× per confirmed finding | Synthesizes prior outputs already in main context into the final brief. |

## Report directory

`/proofread` writes all stage outputs into a single directory in the user's working directory. Default: `proofreader-report/`. The user may override with `out=<path>`. If the directory already exists, ask the user before overwriting — typical resolutions are to rename the old one (`proofreader-report-v1/`) or pass an explicit `out=` flag.

Layout:

```
proofreader-report/
├── report.md                       # top-level summary (final assembly)
├── paper-context.md                # prepare-paper-context output, if invoked
├── evaluation.md                   # Stage 1: evaluate-paper output
├── audits/<label>.md               # Stage 2: per-result audit (one per flagged result)
├── counterexamples/
│   ├── <label>.md                  # Stage 3: CX investigation report
│   └── <label>-*.py                # Stage 3: verification scripts (independently runnable)
├── defenses/<label>.md             # Stage 4: defender output
├── arbiters/<label>.md             # Stage 4: arbiter output
└── findings/<label>.<ext>          # Stage 5: confirmed-finding briefs (Markdown or LaTeX)
```

`<label>` slugs must be filesystem-safe — convert paper-result labels (`Theorem 3`, `Lemma 4.2`) to lowercase-hyphenated form (`theorem-3`, `lemma-4-2`).

Two audiences for the persisted artifacts:

- **The author.** Deliverables (`report.md`, `findings/`) are what they keep and share. Intermediates (`audits/`, `defenses/`, `arbiters/`) are an evidence trail — useful when a coauthor or future-you disputes a verdict, or when a finding is contested and the audit chain needs to be re-examined.
- **`/diff-proofread`.** When run against two report directories from successive draft revisions, it reuses unchanged audits and computes verdict transitions between versions cheaply. This is the structural reason audits are persisted per-result.

Intermediates that *don't* go to disk: the per-skill conversation context (what the orchestrator passes between stages inline) stays in the parent conversation only. The persisted files duplicate that for cross-session, multi-author, and diff use cases.

## Execution

### Cost-discipline preamble

Before launching, give the user a one-line plan and wait for confirmation, unless the user invoked with explicit `confirm`:

> *"Plan: evaluate the paper, audit ~N likely-flagged proofs (one call each), hunt counterexamples on ~M (in subagents), stress-test confirmed findings via fresh defender + arbiter subagents, write up. Expect this to take a while and use a non-trivial amount of tokens — the counterexample subagent iterates Python verification scripts agentically, and the audit / defender / arbiter calls scale with the number of flagged results. Proceed?"*

Do not fabricate specific token-count or wall-time estimates. If the user asks for one, say honestly that the plugin does not yet have calibrated per-paper measurements and the agentic counterexample stage makes per-paper cost highly variable; suggest they monitor their provider's usage dashboard during the run, or invoke `evaluate-paper` alone first to see how many results would escalate to the more expensive stages.

### Stage 1: evaluate-paper

Create the report directory (default `proofreader-report/`, or the path passed via `out=`). If `prepare-paper-context` was run beforehand, save a copy of its output to `proofreader-report/paper-context.md`.

Invoke the `evaluate-paper` skill on `$ARGUMENTS`. This is an inline call — the result lives in the main conversation context. After the skill returns, write the full output to `proofreader-report/evaluation.md`.

From the output, identify *flagged* results — those with `verdict ∈ {uncertain, likely_flawed, flawed}`. This matches the precursor pipeline's escalation threshold. In `adversarial` mode, also escalate `likely_correct` to catch issues the rigorous threshold would miss.

Announce: *"Stage 1 complete: N total results, K flagged for audit. Report directory: <path>"*

### Stage 2: audit-proof per flagged result

For **each** flagged result, invoke the `audit-proof` skill inline. One audit per result, mirroring the precursor pipeline's per-result invocation.

Inputs for each audit:
- The result statement.
- The verbatim proof text (extracted by Stage 1).
- The system model and notation (extracted by Stage 1).
- The Phase-1 concern level and notes.

Audits stay in the main conversation. They're cheap to display and the user benefits from following along.

After each audit returns, write the full audit Markdown to `proofreader-report/audits/<label>.md`. The persisted per-result file is what `/diff-proofread` will reuse on a subsequent revision pass when the proof text is unchanged.

Announce progress: *"Stage 2: auditing Theorem 3 (1/K)…"* as you go.

After all audits, identify:
- **CX candidates**: any flagged audit (verdict `uncertain`, `likely_flawed`, or `flawed`) with at least one issue marked `Counterexample-falsifiable? yes` and `severity ≥ moderate`. **`uncertain` results are included** — a concern the audit could not resolve from the proof text is exactly what a counterexample hunt is for.
- **Stress-test-only candidates**: flagged audits with no falsifiable issue (no useful CX attack surface) — skip CX, but still run defender + arbiter.

**Every flagged result reaches the arbiter.** Whether a result ends up with a constructed counterexample, a counterexample hunt that found nothing, or no falsifiable issue at all, it proceeds to Stage 4 (defender + arbiter) for a final true/false-positive verdict. The pipeline does **not** "recommend a proof rewrite and stop": a flagged result is only ever resolved by an arbiter verdict (`true_positive` / `likely_true_positive` / `likely_false_positive` / `false_positive`) or an explicit `inconclusive`. This guarantees no flagged result is silently dropped without adjudication — even when the arbiter is very likely to find no problem, the run is recorded so the verdict is auditable and the result is not left in limbo.

### Stage 3: find-counterexample (subagent, per CX candidate)

For each CX candidate, dispatch the `find-counterexample` agent via the Agent tool. **Each is a separate subagent invocation** — independent investigations, independent contexts.

Pass `output_dir: proofreader-report/counterexamples/` in the dispatcher prompt so the subagent's verification scripts are written there (rather than the working directory). The script convention becomes `proofreader-report/counterexamples/<label>-<attack-surface>.py`.

If multiple CX candidates exist and they're truly independent, dispatch them in parallel (one Agent tool call per candidate in the same message). If there's only one, dispatch it alone.

Each subagent returns a Markdown counterexample report. Write the returned Markdown to `proofreader-report/counterexamples/<label>.md` and keep a copy in the conversation context for downstream stages.

Announce: *"Stage 3: dispatched N counterexample subagents…"* and report each result as it returns.

#### CX failure → tighter audit re-pass

If a `find-counterexample` subagent returns `outcome: no_counterexample` for an audit that was `likely_flawed`, this is a strong signal that the audit was wrong about result-falsity but may still be right about proof-unsoundness. **Do not silently move on.** Specifically:

1. Re-classify the audit's two-axis verdict to **`result_truth: likely_true`** and **`proof_soundness: unsound` or `unsound_but_recoverable`** (whichever fits the audit's evidence).
2. Re-invoke `audit-proof` inline on the same result with a tighter brief: "The counterexample search failed — the result is probably true. Focus your re-audit on *proof soundness*: which specific step is invalid, and what alternative argument (standard prior result, restricted-quantifier substitution, etc.) would establish the claim?" This second pass produces a sharper diagnosis of the proof-only flaw.
3. Mark the result for Stage 4 stress-test with the new framing — the defender should focus on whether the alternative argument actually closes the gap, not on whether the original proof was sound.
4. Do **not** dispatch another `find-counterexample` on this result. The CX hunt has already failed; the issue is provably not about result-falsity.

This feedback loop targets one of the largest false-positive sources in the original pipeline: audits that flag `likely_flawed` based on perceived proof gaps, then surface a confused arbiter verdict when CX hunt fails. The tightened second pass converts that into a clean "result holds, proof needs rewriting" finding.

### Stage 4: stress-test-defense (defender + arbiter subagents)

For **every** flagged result (`uncertain` / `likely_flawed` / `flawed`) — whether it has a constructed counterexample, a counterexample hunt that returned `no_counterexample`, or no falsifiable issue at all:

1. Dispatch the `defend-finding` subagent with: full paper text, audit, counterexample (if any), mode. When the defense Markdown returns, write it to `proofreader-report/defenses/<label>.md`.
2. **After** the defender returns, dispatch the `arbitrate-finding` subagent with: full paper text, audit, defense, counterexample (if any), mode. When the arbiter Markdown returns, write it to `proofreader-report/arbiters/<label>.md`.

The arbiter must be a separate Agent call — do NOT pass the defender's intermediate context, only its final Markdown output.

If multiple stress-tests are independent, defenders for different results can run in parallel; arbiters must wait for their respective defenders first.

Announce: *"Stage 4: stress-testing N findings…"* and report each verdict.

### Stage 5: writeup-finding (inline, per confirmed finding)

For each result the arbiter verdicted as `true_positive` or `likely_true_positive`, invoke the `writeup-finding` skill inline. Use the format specified in the user's argument (default Markdown for the orchestrator).

Save each writeup to `proofreader-report/findings/<label>.<ext>`.

### Final assembly

Produce `proofreader-report/report.md` — the top-level summary that links to every other artifact in the directory:

```markdown
# Proofreader Report: <paper title>

**Mode**: rigorous | adversarial
**Date**: <ISO date>
**Paper**: <path to input PDF or .tex>

## Summary

- Paper scores: …
- Formal results: <N total>, <K flagged>, <C confirmed flaws>
- **Extraction basis**: latex_source | pdf_text_clean | **pdf_text_with_ocr** — when the input was a PDF and any equation had to be OCR'd from a page image, say so here and point to the OCR transcriptions section below.

Stage outputs: [evaluation](evaluation.md) · [audits/](audits/) · [counterexamples/](counterexamples/) · [defenses/](defenses/) · [arbiters/](arbiters/) · [findings/](findings/)

## OCR-based equations  *(include only when the input was a PDF and at least one equation was OCR'd; omit otherwise)*

Any finding or cleared result whose math was OCR'd from the page image (because `pymupdf4llm` dropped or mangled the equation) is listed here with its OCR transcription record and `Human-check` line, consolidated from the evaluation and audit stages. This is the single place the author checks the OCR'd math against the published PDF.

- **<Result label> — Eq. (N), page P**: `<verbatim OCR transcription>` · **Human-check**: <ambiguous characters, e.g. ceiling-vs-bracket on page P>. → audit: [audits/<label>.md](audits/<label>.md)

## Confirmed findings

For each `true_positive` / `likely_true_positive`:
- **<Result label>**: 1-line description. → [findings/<label>.md](findings/<label>.md) · audit: [audits/<label>.md](audits/<label>.md) · arbiter: [arbiters/<label>.md](arbiters/<label>.md)

## Open questions

For each `inconclusive` arbiter verdict:
- **<Result label>**: what evidence would resolve it (typically a reference to retrieve). → [arbiters/<label>.md](arbiters/<label>.md)

## Dismissed concerns

For each `likely_false_positive` / `false_positive`:
- **<Result label>**: brief reason the audit's concern did not hold up. Useful record so future-you doesn't accidentally re-flag. → [arbiters/<label>.md](arbiters/<label>.md)

## Audits without falsifiable concerns (proof-style / expository only)

For each result flagged in Stage 1 where Stage 2 found only proof-style/expository issues (no falsifiable counterexample surface):
- **<Result label>**: list the suggested proof rewrites. CX was skipped (nothing to falsify), but the defender + arbiter still ran — the arbiter verdict is the resolution. → arbiter: [arbiters/<label>.md](arbiters/<label>.md) · audit: [audits/<label>.md](audits/<label>.md)
```

## Communication discipline

- Announce each stage before starting it. Keep updates terse.
- **PDF input**: ensure `prepare-paper-context` / `evaluate-paper` OCR'd any equation the parser dropped or mangled (Formula fidelity `ocr`). When the run rests on OCR'd math, set the report's Extraction basis to `pdf_text_with_ocr` and populate the OCR-based equations section so the author can spot-check the transcriptions. Never let a verdict on a load-bearing equation flow through on the parser's broken text.
- If a stage produces zero candidates for the next stage, skip and say so.
- If a subagent fails or returns an error, surface it; do not silently move on.
- If the user's tool doesn't support subagents (Stages 3 and 4), warn the user that independence will be degraded and offer to run those stages inline with a clear `independence: degraded` flag in the report.
