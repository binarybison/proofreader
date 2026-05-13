# Proofreader

> **P**roofreader **R**easoning **O**n **O**versight **F**laws — **R**igorous **E**xamination **A**nd **D**isproof **E**valuation **R**outine

A set of LLM skills for **rigorously self-proofreading** real-time systems (and other formal) papers before you submit them. Designed for the author who wants to find the holes in their own proofs before a reviewer does.

> "Proofreading" here means scrutinizing the *correctness of the formal arguments* — not just typo-hunting, and **not** mechanized proof checking in Lean / Rocq / Coq. This is human-language proof scrutiny, executed by an LLM with optional Python code execution for counterexample search.

## What it does

Three **inline skills** (run in the main conversation), three **subagents** (fresh isolated context), and two **slash-command orchestrators**.

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
| `defend-finding` | Mounts the strongest legitimate defense of the paper against an audit finding. Fresh context means the defender has no idea about the eventual arbiter — and no incentive to soften its case in anticipation. |
| `arbitrate-finding` | Impartial adjudicator. Reads paper + audit + defense (+ optional counterexample) with **fresh eyes** and renders a true/false-positive verdict with a flaw taxonomy. |

### Slash commands

| Command | What it does |
|---|---|
| `/stress-test-defense <result>` | Dispatches the defender subagent, then the arbiter subagent, then synthesizes their outputs. Use when you want to gut-check whether an audit finding is real. |
| `/proofread <paper.pdf>` | Full pipeline: `evaluate-paper` → `audit-proof` (per flagged result) → `find-counterexample` (per likely-flawed audit, in subagents) → `defend-finding` + `arbitrate-finding` (in subagents) → `writeup-finding`. Single Markdown report at the end. |

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

Once installed in Claude Code:

```text
> /proofread papers/my-rtss-submission.pdf
```

…or, more granularly:

```text
> Use evaluate-paper on @papers/my-rtss-submission.pdf in rigorous mode.
> Now audit the proof of Theorem 3 in adversarial mode.
> Try to find a counterexample to Lemma 4.
> Stress-test the audit's claim against Lemma 4 — be the harshest reviewer you can.
> Write up the finding on Lemma 4 as a LaTeX brief.
```

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

## Provenance

These skills were distilled from a research pipeline ([Ward, 2026, in preparation](https://github.com/bcward/paper-evaluation)) that uses LLMs as first-pass peer reviewers across published RT systems papers. The author-facing variants in this plugin emit human-readable Markdown instead of pipeline-bound JSON, and the formal-result inventory and per-result audit are split into separate skills, while the adversarial author-defense and arbiter stages are run as fresh-context subagents — the same structural independence the original pipeline gets from making each role a separate API call.

## How to cite

If `proofreader` contributes to a paper of yours — whether by catching an issue you fixed before submission, or as the methodology in a paper-about-papers — please cite the source pipeline:

```bibtex
@misc{ward2026proofreader,
  author = {Ward, Bryan C.},
  title  = {{Proofreader}: {R}easoning {O}n {O}versight {F}laws --
            {R}igorous {E}xamination {A}nd {D}isproof {E}valuation {R}outine},
  year   = {2026},
  note   = {LLM-assisted self-proofreading for real-time systems papers;
            derived from the paper-evaluation pipeline},
  url    = {https://github.com/binarybison/proofreader}
}
```

Replace this entry with the formal venue citation once the underlying methodology paper is published.

## License

MIT — see [LICENSE](LICENSE). Pull requests welcome.
