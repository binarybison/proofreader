---
description: Dispatches a fresh defender subagent and a fresh arbiter subagent to stress-test an audit finding. Each runs in isolated context for genuine independence — defender doesn't know about the arbiter, arbiter wasn't involved in producing the defense.
argument-hint: <result-label> [mode=rigorous|adversarial]
---

# /stress-test-defense

Stress-test an audit finding by running fresh defender and arbiter subagents and synthesizing their outputs.

User argument: `$ARGUMENTS`. Parse the result label (e.g. "Theorem 3", "Lemma 4.2") and optional `mode=rigorous|adversarial`. Default mode is `rigorous`.

## Why this exists as two subagents, not one

The point of running defender and arbiter separately is **structural independence**. The defender's incentive is to defend; if the same agent had to render the final verdict, the defense would be weaker (the model anticipates rebutting itself). The arbiter's value comes from fresh eyes; if it had just produced the defense, it would anchor on that framing.

Running both as subagents in the *same* invocation of this command:
- Preserves their independence (each has its own context).
- Keeps the noisy intermediate work out of the user's main conversation.
- Produces a single synthesized report at the end.

## Steps

### 1. Gather the inputs

The audit and (optionally) counterexample for the target result must already exist in the conversation context, or you should ask the user to point you at them. Required inputs:
- Audit Markdown (from `audit-proof`).
- Paper text or PDF path.

Optional but improves quality:
- Counterexample report (from `find-counterexample`).
- System model and notation extracted earlier.

If anything required is missing, ask the user once, then proceed.

### 2. Dispatch the defender

Use the Agent tool to spawn the `defend-finding` subagent. Pass it:
- The full paper text (or path).
- The audit (verbatim).
- The counterexample report if available.
- The mode.

Wait for the defense Markdown to return.

### 3. Dispatch the arbiter

Use the Agent tool to spawn the `arbitrate-finding` subagent. Pass it:
- The full paper text (or path).
- The audit (verbatim).
- The defense (verbatim, just returned from step 2).
- The counterexample report if available.
- The mode.

The arbiter must be a **separate** Agent invocation — do not nest it inside the defender, do not give it the defender's reasoning trace. It should read the defense as a document, not as a continuation of a thought.

Wait for the arbiter Markdown to return.

### 4. Synthesize and report

Present a top-level summary to the user:

```markdown
# Stress-Test: <result label>

**Mode**: <mode>
**Arbiter verdict**: <verdict>
**Confidence**: <confidence>

## Bottom line

1–3 sentences summarizing the arbiter's verdict rationale.

## Defense (full text)

<full defender output>

## Arbiter verdict (full text)

<full arbiter output>

## Recommended action

What the user should do next, derived from the arbiter's recommended actions:
- If `true_positive` / `likely_true_positive`: recommend running `writeup-finding`.
- If `inconclusive` with unresolved dependencies: list the references to retrieve.
- If `likely_false_positive` / `false_positive`: state the audit's concern doesn't hold up, summarize the dismissal reasoning for the record.
```

Keep the full defender and arbiter outputs included verbatim — the user wants to see both sides' reasoning, not just the verdict.

## Tool fallback

If the running tool does not expose the Agent / Task tool (e.g., a tool without subagent support):

1. Inform the user that running defender + arbiter in the same context loses the independence property.
2. Offer two options:
   - **Option A (recommended)**: open two fresh conversations in the tool, paste [agents/defend-finding.md](agents/defend-finding.md) into one and [agents/arbitrate-finding.md](agents/arbitrate-finding.md) into the other, run them sequentially.
   - **Option B**: degrade gracefully — run both agent prompts inline in the current conversation, but mark the output as `independence: degraded` so the user knows the verdict is less reliable than the canonical chain.
