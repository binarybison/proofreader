# rt-proofreader

A set of LLM skills for **rigorously self-proofreading** real-time systems (and other formal) papers before you submit them. Designed for the author who wants to find the holes in their own proofs before a reviewer does.

> "Proofreading" here means scrutinizing the *correctness of the formal arguments* — not just typo-hunting, and **not** mechanized proof checking in Lean / Rocq / Coq. This is human-language proof scrutiny, executed by an LLM with optional Python code execution for counterexample search.

## What it does

Five skills, chainable:

| Skill | What it does |
|---|---|
| `evaluate-paper` | First-pass read: quality scores, flags, list of all theorems/lemmas with per-result verdicts. |
| `audit-proof` | Deep audit of one theorem or lemma. Lists issues by severity. |
| `find-counterexample` | Agentic counterexample hunt for a flagged result. Writes and runs Python to verify. |
| `stress-test-defense` | For a flagged result, generates the strongest defense AND the strongest rebuttal, then renders an honest verdict. Use this as a sanity check before you dismiss an issue. |
| `writeup-finding` | Produces a clean LaTeX or Markdown brief of a finding — useful to share with coauthors or to keep as a record. |

Plus one orchestrator:

| Command | What it does |
|---|---|
| `/proofread <paper.pdf>` | Runs `evaluate-paper` → `audit-proof` (on every flagged result) → `find-counterexample` (on every `likely_flawed` audit) → `stress-test-defense` → `writeup-finding`. Single Markdown report at the end. |

Every skill has a **`mode`** knob:

- **`rigorous`** (default): flags issues clearly with severity, always suggests a fix or follow-up. Reviewer tone for journal/conference feedback.
- **`adversarial`**: red-team the paper. Don't give yourself the benefit of the doubt. Useful for self-review where you want to break your own work before someone else does.

You set the mode by including `mode: adversarial` (or `mode: rigorous`) in your request, e.g. *"Audit the proof of Theorem 3 in adversarial mode."*

## Installation

### Claude Code (recommended)

This repo is a Claude Code plugin. Two ways to install:

**From a local clone** (fastest for iterating on the plugin):

```bash
git clone https://github.com/bcward/rt-proofreader.git ~/rt-proofreader
# Then from inside any Claude Code project:
/plugins install ~/rt-proofreader
```

**From a marketplace** (once published):

```bash
/plugins marketplace add bcward/rt-proofreader
/plugins install rt-proofreader@bcward
```

After install, the five skills auto-load on relevant prompts, and `/proofread` is available as a slash command.

### Codex CLI, Gemini CLI, or any other LLM tool

The skill files are plain Markdown with YAML frontmatter. To use one in another tool:

1. Open `skills/<skill-name>/SKILL.md`.
2. Copy the body (everything after the `---` frontmatter block) into your tool as a system or user prompt.
3. Append your input (paper text, proof text, etc.) where the body's `## Inputs` section indicates.

For tools that support custom prompts as files (e.g. Codex `--prompt-file`, Gemini `@file`), reference the `SKILL.md` directly — the YAML frontmatter is benign and most tools ignore it.

The `find-counterexample` skill assumes the tool can execute Python. Most CLI coding tools support this; for tools that don't, the skill produces a Python script you can run yourself.

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
- **Partially in scope**: experimental / systems papers — `evaluate-paper` gives useful quality scores, but the audit/CX skills shine on proofs.
- **Out of scope**: formal verification in proof assistants (use Lean / Rocq / Isabelle for that). This is *natural-language* proof scrutiny.

## Provenance

These skills were distilled from a research pipeline ([Ward, 2026, in preparation](https://github.com/bcward/paper-evaluation)) that uses LLMs as first-pass peer reviewers across published RT systems papers. The author-facing variants in this plugin emit human-readable Markdown instead of pipeline-bound JSON, and merge the pipeline's adversarial author-defense + arbiter stages into a single `stress-test-defense` skill.

## License

MIT. Pull requests welcome.
