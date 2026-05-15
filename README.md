# Proofreader

An agentic LLM tool for pre-submission self-review of formal proof-based papers. Designed for the author who wants to find the holes in their own proofs before a reviewer — or a later reader — does.

> The name is a deliberate double entendre: the tool proofreads, in the copy-editor's sense, by reading proofs, in the formal sense.

> "Proofreading" here means scrutinizing the *correctness of the formal arguments* — not just typo-hunting, and **not** mechanized proof checking in Lean / Rocq / Coq. This is human-language proof scrutiny, executed by an LLM with optional Python code execution for counterexample search. Proofreader screens; it does not certify. Its output is stochastic and *neither sound nor complete* — it can flag results erroneously, and it can miss flaws entirely. We have nonetheless found it useful, including in cases where independent authors confirmed the findings.

## What it does

Three **inline skills** (run in the main conversation), four **subagents** (fresh isolated context), and three **slash-command orchestrators**.

### Inline skills

| Skill | What it does |
|---|---|
| `evaluate-paper` | First-pass read: quality scores, flags, complete inventory of theorems/lemmas with per-result verdicts. One call per paper. |
| `audit-proof` | Deep audit of one theorem or lemma. Lists issues by severity. The orchestrator calls this **once per flagged result** (mirroring the original pipeline). |
| `writeup-finding` | Produces a clean LaTeX or Markdown brief of a finding — share with coauthors or keep as a record. |

### Subagents

These run in fresh, isolated contexts. The main conversation dispatches them and receives a single report back. The structural independence matters for correctness (see [Why subagents?](#why-subagents) below).

| Agent | What it does |
|---|---|
| `find-counterexample` | Adversarial CX hunt for a flagged result. Writes and runs Python to verify. Isolated context keeps the noisy iteration out of the main conversation. |
| `defend-finding` | Mounts the strongest legitimate defense of the paper against an audit finding. Fresh context means the defender has no idea about the eventual arbiter — and no incentive to soften its case in anticipation. May fetch cited references with explicit user permission. |
| `arbitrate-finding` | Impartial adjudicator. Reads paper + audit + defense (+ optional counterexample) with **fresh eyes** and renders a true/false-positive verdict with a flaw taxonomy. |
| `verify-restatement` | When the paper restates a theorem from a cited source (`Theorem 1 (Liu-Layland)`), fetches the original (with permission) and compares — detects precondition drift, conclusion strengthening, quantifier-scope changes that propagate through the paper's downstream proofs. |

### Slash commands

| Command | What it does |
|---|---|
| `/proofread <paper.pdf>` | Full pipeline: `evaluate-paper` → `audit-proof` (per flagged result) → `find-counterexample` (per likely-flawed audit, in subagents) → `defend-finding` + `arbitrate-finding` (in subagents) → `writeup-finding`. Single Markdown report at the end. |
| `/stress-test-defense <result>` | Dispatches the defender subagent, then the arbiter subagent, then synthesizes their outputs. Use when you want to gut-check whether an audit finding is real. |
| `/diff-proofread <old> <new>` | Compares two versions of a draft and reports what was fixed, what regressed, what's new, and what's unchanged. Use it across revision rounds to confirm fixes took and to catch regressions early. |

### Why subagents?

The defender, arbiter, and counterexample-hunter are subagents (not inline skills) for one reason: **structural independence**. The original paper-evaluation pipeline got independence for free by making each role a separate API call; the plugin recreates that property via fresh-context subagents.

- The **defender** has an asymmetric incentive to defend. If it knew the arbiter would later rebut it in the same context, it would soften its case. Fresh context preserves the asymmetric incentive.
- The **arbiter** brings genuine independent judgment because it never produced the audit *or* the defense — it reads both as documents.
- The **counterexample hunt** is long, iterative, and Python-heavy. Isolating it keeps the noise out of the main conversation.

If your tool doesn't support subagents (Codex/Gemini in some configurations), the orchestrators degrade gracefully and mark the report `independence: degraded`.

Every skill has a **`mode`** knob:

- **`rigorous`** (default): flags issues clearly with severity, always suggests a fix or follow-up. Reviewer tone for journal/conference feedback.
- **`adversarial`**: red-team the paper. Don't give yourself the benefit of the doubt. Useful for self-review where you want to break your own work before someone else does.

You set the mode by including `mode: adversarial` (or `mode: rigorous`) in your request, e.g. *"Audit the proof of Theorem 3 in adversarial mode."*

## Installation

### Claude Code (recommended)

This repo is a Claude Code plugin. Two ways to install:

**From a local clone** (fastest for iterating on the plugin):

```bash
git clone https://github.com/binarybison/proofreader.git ~/proofreader
# Then from inside any Claude Code project:
/plugins install ~/proofreader
```

**From a marketplace** (once published):

```bash
/plugins marketplace add binarybison/proofreader
/plugins install proofreader@binarybison
```

After install, skills auto-load on relevant prompts; subagents are dispatchable by the orchestrators or by name; `/proofread` and `/stress-test-defense` are available as slash commands.

### Codex CLI, Gemini CLI, or any other LLM tool

The skill, agent, and command files are all plain Markdown with YAML frontmatter. To use one in another tool:

1. Open the relevant file: `skills/<name>/SKILL.md`, `agents/<name>.md`, or `commands/<name>.md`.
2. Copy the body (everything after the `---` frontmatter block) into your tool as a system or user prompt.
3. Append your inputs (paper text, audit, etc.) where the body indicates.

For tools that support custom prompts as files (Codex `--prompt-file`, Gemini `@file`), reference the file directly — the YAML frontmatter is benign and most tools ignore it.

**Subagent independence in tools without subagents**: the defender / arbiter / counterexample-hunter rely on running in *separate, fresh contexts* — that's how the plugin matches the original paper-evaluation pipeline's quality on adversarial review. If your tool doesn't have a subagent primitive, the canonical workaround is to **open separate conversations** for `defend-finding` and `arbitrate-finding`, paste the agent body into each, and run them sequentially. Running them inline in one chat works as a fallback but is structurally weaker — mark such results `independence: degraded` in your writeup.

The `find-counterexample` agent assumes the tool can execute Python. Most CLI coding tools support this; for tools that don't, the agent produces a Python script you can run yourself.

## Quick start

The fastest path, end-to-end:

```text
> /proofread papers/my-rtss-submission.pdf
```

But every skill, agent, and command is independently invokable. The two workflows below show the typical end-to-end stories; the patterns after them cover narrower one-off uses.

## Workflows

### Pre-submission self-review

The intended workflow: you have a draft, you want to find the holes before a reviewer does.

1. **Hand it the LaTeX source if you have it.** Theorem-environment boundaries, math symbols, and `\label`/`\ref` topology survive LaTeX extraction exactly; PDF extraction is heuristic and lossier. Run `prepare-paper-context` once at the start of the session so downstream skills don't re-parse.
2. **Run the full pipeline in adversarial mode.**
   ```text
   > /proofread papers/my-draft.tex mode=adversarial out=proofreader-report-v1/
   ```
   The orchestrator prints a per-stage plan and waits for confirmation before launching. Expect this to take a while and use a non-trivial amount of tokens: the audit stage runs once per flagged result, the counterexample subagent iterates Python verification scripts agentically until it succeeds or exhausts its attack-surface list, and the defender / arbiter chain runs separately per finding. Variance is large — a paper with two clean theorems is much cheaper than one with eight contested ones. Watch your provider's usage dashboard if cost matters. Adversarial mode is the right setting here: you want the worst plausible reading of your own work, so you can decide what to harden *before* submission.

   The output is a directory containing `report.md` (the top-level summary), per-result audits, counterexample reports and verification scripts, defender and arbiter outputs, and one finding brief per confirmed flaw. Naming the directory with a version suffix (`v1`, `v2`, …) makes step 6 below cheap.
3. **Triage findings as they come back.** For each `true_positive` / `likely_true_positive`, decide: is the fix a tightened precondition, a proof rewrite, or a result revision? The two-axis verdict (result truth vs. proof soundness) tells you which.
4. **Inject the findings into your source.** Run `annotate-latex` to write `% PROOFREADER` comments at the affected proof environments and labeled equations. The comments don't affect the rendered PDF, but they show up next to the proof text in your editor.
5. **Revise in your normal editor workflow.** Address one annotation at a time; remove it (or delete it via the `sed` line in the index file) as you fix the underlying issue.
6. **Verify the fixes took.** First run `/proofread` on the revised draft into a fresh directory:
   ```text
   > /proofread papers/my-draft.tex mode=adversarial out=proofreader-report-v2/
   ```
   Then diff the two report directories:
   ```text
   > /diff-proofread proofreader-report-v1/ proofreader-report-v2/
   ```
   `/diff-proofread` reuses per-result audits whose verbatim proof text didn't change between versions — only the touched proofs are re-audited, which keeps revision rounds cheap. The diff report leads with regressions (the highest-priority signal — your fix introduced a new problem), then fixes, unfixed issues, and new findings.
7. **Iterate** if regressions or new findings appear; otherwise submit.

A useful habit: keep the proofreader report directories under version control alongside the draft. The audit history becomes a record you can hand to coauthors or future-you, and `/diff-proofread` only pays the LLM cost for proofs that actually changed.

### Reviewing your past publications

The retrospective workflow: you want to audit results you've already published — to issue errata, inform follow-up papers that build on those results, or sharpen your own sense of what patterns to scrutinize harder in current drafts.

1. **Pick what to review, in priority order.** Token cost compounds across a publication record, so don't bulk-run blindly. Prioritize: results that downstream papers (yours or others') rely on; headline theorems whose retraction would matter; anything where you've had a nagging doubt; restated theorems from prior work (these are high-leverage for `verify-restatement`).
2. **Use the LaTeX source if you still have it; otherwise the PDF.** PDF extraction is lossier for older papers — surface any mangled equations from `evaluate-paper`'s extraction warnings before trusting the verdicts. If a paper's `.tex` source is still on disk, prefer it.
3. **Run `/proofread mode=adversarial`** on each paper. Same rationale as pre-submission: you want the harshest plausible reading, the way a reader might find an issue later.
4. **Let the defender / arbiter chain filter false positives.** Older papers tend to defer proofs to companion technical reports, appendices on author webpages, or follow-up journal versions; the `defend-finding` subagent can fetch those (with your permission) and surface defenses the audit missed. Trust the arbiter's `true_positive` / `likely_true_positive` verdicts — the chain is designed to be conservative against the audit.
5. **Cross-check against any existing public errata** before treating a finding as novel. Some issues may already be acknowledged by you, a coauthor, or a follow-up paper.
6. **Selectively run `verify-restatement`** on theorems your paper restated from prior work. Precondition drift and conclusion strengthening in restatements are a common, hard-to-spot flaw family that propagates as if it were the original result.
7. **Decide what to do with each confirmed finding.** Options, in roughly increasing severity: a private note for future-you; a footnote in a successor paper; an entry on your public errata page; a formal erratum to the venue; in rare cases, contacting authors who cited the affected result. `writeup-finding` will draft a clean LaTeX or Markdown brief for any of these.

The compounding value: even findings you choose not to act on tighten your intuition for the next paper. The flaw patterns Proofreader catches in your past work are typically the same ones it will catch in your next draft — and over time you internalize them.

## Patterns beyond `/proofread`

### Pattern 1 — Single-theorem counterexample hunt

You suspect one specific result. Skip everything else; just try to break it.

```text
> Use find-counterexample on Theorem 3 of papers/baruah-sies24.pdf.
>   Theorem 3 states: "<paste statement>"
>   Proof: "<paste verbatim proof>"
>   System model: implicit-deadline sporadic task set, m identical processors,
>     non-preemptive global scheduling.
```

The `find-counterexample` agent dispatches to a fresh subagent, identifies attack surfaces from the proof, writes Python verification scripts to your working directory, iterates, and returns one Markdown report. No evaluation, no audit, no orchestrator.

If you've already done the audit by hand and know the suspect step:

```text
> Use find-counterexample on Theorem 3. The suspicious step is the inductive
>   chain that substitutes R⁻ for R⁺ on line 4 of the proof. Try parameter
>   regimes where this gap is amplified.
```

The agent uses your hint as the primary attack surface and works from there.

### Pattern 2 — Audit one proof you just wrote

You're not sure about a single proof in your own draft. Skip the whole-paper inventory.

```text
> Use audit-proof in adversarial mode on the proof of Lemma 4 below.
>   Statement: "<paste>"
>   Proof: "<paste>"
>   System model: "<paste>"
>   Notation: <list>
```

Returns the issue list with severities. If any issue is `Counterexample-falsifiable? yes` at moderate severity or worse, follow up with Pattern 1.

### Pattern 3 — Stress-test a finding you already have

A coauthor flagged an issue. You want the defender + arbiter chain to decide whether it's real before you edit the paper. Skip the audit and CX stages.

```text
> /stress-test-defense Theorem 3 mode=adversarial
>
> Audit: "<paste audit description from coauthor>"
> Counterexample (if any): "<paste or 'none'>"
> Paper: papers/my-draft.pdf
```

This dispatches the `defend-finding` subagent first (fresh context, instructed to mount the strongest legitimate defense), then dispatches `arbitrate-finding` as a separate subagent that reads the defense as a document and renders an independent verdict. You get both sides plus a verdict with confidence and flaw taxonomy.

### Pattern 4 — First-pass triage only

You want quality scores and a theorem inventory to decide where to submit, but not the deep audit yet.

```text
> Use evaluate-paper on @papers/my-draft.pdf in rigorous mode.
```

Returns the report with per-result verdicts. Stop here if nothing flagged worse than `likely_correct`. Run `audit-proof` on the items that came back `uncertain` or worse.

### Pattern 5 — Counterexample against a competitor's claim

You're writing a paper and want to argue that a prior work's bound is loose (or unsafe). Use Proofreader on *their* paper, not yours.

```text
> Use find-counterexample on Equation 7 of papers/prior-work-ecrts23.pdf.
>   The paper claims this is a safe upper bound on response time under
>   global EDF with self-suspensions. I think it omits the self-suspension
>   delay penalty entirely; try task sets with long suspensions.
```

If the agent finds a counterexample, run `writeup-finding` to draft the LaTeX brief you'd put in your related-work section.

### Pattern 6 — Generate the writeup from existing data

You already did the audit and built the counterexample manually. You just want the brief.

```text
> Use writeup-finding in latex format.
>   Result: Theorem 3 of my paper.
>   Audit summary: "<paste>"
>   Counterexample parameters: { τ₁: C=2 T=5 D=5, τ₂: C=3 T=7 D=7 }
>   Verification: ran 100k-cycle simulation; observed deadline miss at t=14.
>   Decided: revise theorem to add precondition D_i ≤ T_i / 2.
```

Returns a compilable LaTeX brief. Useful as a starting draft for an erratum, an internal memo, or a paper revision note.

### Pattern 7 — Audit chained with stress-test, skipping CX

The audit found a proof-style critique (gaps, unclear steps) but no falsifiable claim. CX search would waste effort; you still want the adversarial review.

```text
> Use audit-proof on Lemma 2 in adversarial mode.
>   <inputs>
> The audit returned likely_flawed but all issues are Counterexample-falsifiable? no.
> Run /stress-test-defense on this audit with no counterexample.
```

The defender will focus on whether the gaps are presentation-only or load-bearing (apply the four-question filter from `audit-proof`); the arbiter will weigh that against the audit's claims.

### Pattern 8 — Defense-only, anticipate referee objections

You want to know how a sympathetic but honest reader would defend your paper against a likely referee objection. Skip the arbiter step.

```text
> Use defend-finding on the following hypothetical objection:
>   "Theorem 5's proof implicitly assumes the schedule is work-conserving,
>    which contradicts the paper's claim to handle non-work-conserving policies."
> Paper: @papers/my-draft.pdf
```

The defender returns the strongest legitimate defense plus an `acknowledged flaws` section if any of the objection lands. Useful pre-submission to decide whether to harden the proof or revise the claim.

### Pattern 9 — Parallel audit of multiple independent theorems

For a paper with several theorems you want audited independently:

```text
> Audit Theorem 3, Theorem 5, and Lemma 7 of @papers/my-draft.pdf in
>   adversarial mode. Run them in parallel where possible.
```

Each audit runs inline in the main conversation (so you can follow along), but Claude Code dispatches independent calls concurrently where the tool allows.

### Pattern 10 — Harshest-plausible self-review

You want the worst plausible interpretation of your own draft, so you can decide what to harden before submission rather than after:

```text
> /proofread papers/my-draft.pdf mode=adversarial
```

Adversarial mode tightens `evaluate-paper`'s thresholds (cast a wide net during triage) and instructs the arbiter to break ties against the paper. Use this as your pre-submission "be the harshest reviewer you can" pass.

## Composition with other tools

Proofreader is deliberately scoped to formal-proof scrutiny (see [Scope](#scope) below). For a complete pre-submission pass, chain it with a general writing-quality review:

```text
> /proofread papers/my-draft.pdf
> [review confirmed findings, revise the paper]
> /review papers/my-draft.pdf            # Anthropic's general /review skill
> [revise prose, organization, related work]
```

Run Proofreader first because correctness issues usually require larger revisions than prose issues, and prose review on a still-changing draft wastes effort.

## Scope

- **In scope**: papers whose contributions are formal — scheduling-theoretic, response-time analysis, network-calculus, (min,+) algebra, real-time queueing, control-theoretic bounds.
- **Partially in scope**: experimental / systems papers — `evaluate-paper` gives useful quality scores, but the audit and counterexample skills shine on proofs.
- **Out of scope**: formal verification in proof assistants (use Lean / Rocq / Isabelle for that). This is *natural-language* proof scrutiny.
- **Deliberately out of scope: general writing-quality review** — see below.

### Why general writing-quality review is out of scope

Proofreader is intentionally narrow. It does not comment on prose clarity, abstract structure, introduction motivation, related-work coverage, citation formatting, figure design, or the dozens of other dimensions that go into a well-written paper. Three reasons:

1. **Distinctiveness.** Proofreader's value is rigorous formal-proof scrutiny. The moment it also weighs in on prose and exposition, that signal gets diluted — peers stop trusting that a "this paper looks good" verdict means the *proofs* look good, because it now folds in writing quality. A tool that tries to do everything ends up being weakly trusted on each thing.

2. **Composition over monoliths.** Anthropic's `/review` skill (and many third-party writing-quality plugins) already cover general paper review well. The intended workflow is to chain them: run Proofreader for proof rigor → run a general review tool for exposition → revise. You do not need both inside one tool, and forcing them together makes both jobs worse.

3. **Audience.** Proofreader's audience is senior researchers who already have peer review, coauthors, and decades of writing practice for prose-quality feedback. What they cannot easily get is an adversarial reviewer who will catch a wrong-direction `R⁻`/`R⁺` substitution three pages deep in an induction chain, or a constant assumed to equal 1 when the paper's own measurement table reports it ranges to 1.095. That is the gap Proofreader fills.

If you want general writing review, run a separate tool. If you want proof scrutiny, run Proofreader.

## Domain packs

Proofreader's flaw-pattern coverage is extensible via [`domain-packs/`](domain-packs/). The baseline `scheduling-theory` pack covers classical RT scheduling; `network-calculus` is a starter pack; packs for control-theoretic bounds, probabilistic real-time, distributed RT, DAG-parallel, and shared-resource analysis are planned. Contribute a pack hand-written or generated mechanically from a subfield-specific flaw corpus — see [domain-packs/README.md](domain-packs/README.md).

## LaTeX support

Proofreader accepts `.tex` source as a first-class input format, alongside PDF. The `prepare-paper-context` skill normalizes either form into a clean representation; `annotate-latex` injects audit findings as in-place `\todo{}` or `% PROOFREADER` comments in your source so you can address them in your normal editor workflow. See those skills' SKILL.md files for details.

## Provenance

Proofreader is described in *Proofreader: An Agentic LLM Tool for Auditing Proof-Based Papers* ([Ward, 2026, manuscript](https://github.com/binarybison/proofreader)). The plugin's flaw-pattern library is empirically grounded — it was distilled from a retrospective screening pass over a corpus of real-time systems papers, in which a precursor pipeline acted as a mechanical first-pass reviewer to surface candidate flaws for human follow-up. Proofreader is the author-facing evolution of that work: rather than screening published papers retrospectively, it is meant to be run by authors on their own drafts (or their own prior work), before a reviewer or later reader has the chance to find the same issues. The skills in this plugin produce human-readable Markdown instead of pipeline-bound JSON, split the inventory and per-result audit into separately invocable skills, and run the defender and arbiter stages as fresh-context subagents — the same structural independence the precursor pipeline obtained by making each role a separate API call.

## How to cite

If Proofreader contributes to a paper of yours — whether by catching an issue you fixed before submission, or as the methodology in a paper-about-papers — please cite:

```bibtex
@misc{ward2026proofreader,
  author = {Ward, Bryan C.},
  title  = {{Proofreader}: An Agentic {LLM} Tool for Auditing
            Proof-Based Papers},
  year   = {2026},
  note   = {Manuscript; Claude Code plugin for pre-submission
            self-review of formal proof-based papers},
  url    = {https://github.com/binarybison/proofreader}
}
```

Replace this entry with the formal venue citation once the paper is published.

## License

MIT — see [LICENSE](LICENSE). Pull requests welcome.
