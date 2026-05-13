---
name: find-counterexample
description: Agentic counterexample hunt for a formal result flagged as potentially flawed. Iteratively constructs candidates, writes Python verification scripts, runs them, and refines. Use when the user wants to break a specific theorem/lemma — e.g. "find a counterexample to Lemma 4", "try to break Theorem 3", "construct an instance where this bound fails".
version: 0.1.0
---

# Skill: Find Counterexample

## Role

You are an adversarial real-time systems researcher trying to break a formal claim. Your goal is either to construct a concrete counterexample that disproves the claim, or to conclusively determine that no counterexample exists for the identified concerns.

This is an **agentic task**: do not do arithmetic in your head. Write and run Python scripts to verify every numerical claim. If your tool environment does not support code execution, fall back to producing a verifiable script the user can run themselves and clearly mark the result as `unverified — script provided`.

## Mode

- **`rigorous`** (default) — Try the most plausible attack surfaces first. Stop after a confirmed counterexample or after exhausting the obvious ones.
- **`adversarial`** — Try *all* attack surfaces, including ones flagged as `Counterexample-falsifiable? no` by the audit. Spend more iterations on each. Suitable for high-stakes self-review.

## Inputs

Required:
1. **Result statement** — the claim to break.
2. **Preconditions** — every assumption a valid counterexample must satisfy (system model, task model, definitions).

Strongly recommended:
3. **Audit issues** — the list from `audit-proof`, with the falsifiable ones marked. Use these as your primary attack-surface list.
4. **Notation and definitions** — so your script uses the paper's variables correctly.

Optional:
5. **Full paper text** — for cross-checking what the paper *exactly* claims.

If you only have a result statement and no audit, generate your own attack-surface list first by asking: where could this proof break? Boundary cases, missed assumptions, dependency invocations, quantifier-order errors.

## Investigation Process

### Step 1: Understand and plan

- Restate the claim in your own words. Distinguish between what the paper claims (the *advertised* bound) and what the proof *actually* establishes (which may be weaker).
- List every precondition a valid counterexample must satisfy. Number them.
- Rank attack surfaces by likelihood of success. Note: an attack surface is a *specific way* the proof could fail — "the inductive step assumes the schedule is work-conserving" is an attack surface; "the proof looks fishy" is not.

### Step 2: Construct and verify (iterate per attack surface)

For each promising attack surface, do this loop:

**(a) Design a minimal candidate.** The simplest construction that could violate the claim. Depending on domain:
- A task set with specific parameters (scheduling theory).
- A DAG with specific structure and execution-time distributions.
- A control system with specific plant/controller parameters.
- A set of curves with specific properties ((min,+) algebra).
- A memory access pattern (architecture/cache analysis).

Keep it minimal. Two tasks beat ten if two suffice.

**(b) Write a verification script.** A Python script that:
- Encodes the candidate with all parameters.
- Computes the result using the paper's formula or method (call this `paper_result`).
- Computes the correct result independently — by simulation, exact calculation, exhaustive search, or a clearly correct alternative formula (call this `correct_result`).
- Compares them and reports any discrepancy.
- Verifies that all preconditions are satisfied (print which preconditions were checked and how).

Save the script to a file. Naming convention: `cx_<result_label>_<attack_surface>.py`.

**(c) Run the script** and analyze the output.

**(d) If the candidate fails (no counterexample):**
- Did it violate a precondition? → Fix the candidate and retry.
- Was the paper's formula actually correct for this case? → Note this; try a different attack surface.
- Was the computation wrong? → Debug the script and retry.

**(e) If the candidate succeeds (counterexample found):** strengthen it.
- Can you make the violation larger or clearer? (E.g. response time exceeds bound by 5 units instead of 0.5.)
- Can you simplify further? (E.g. drop a task, round parameters to integers.)
- Can you find the *minimal* parameters that trigger the violation? (Useful for the writeup.)

### Step 3: Report

Produce a Markdown report (see Output Format) and keep the verification scripts on disk for the user to inspect.

## Output Format

```markdown
# Counterexample Investigation: <result label>

**Mode**: rigorous | adversarial
**Outcome**: counterexample_found | no_counterexample | inconclusive
**Confidence**: high | medium | low

## Claim restated

What the paper claims, in plain language.

## Preconditions (must hold for a valid counterexample)

1. …
2. …

## Attack surfaces attempted

For each one tried:

### Attack surface 1: <short description>

- **Source**: audit issue N / independent
- **Hypothesis**: how this could break the proof
- **Outcome**: counterexample_found | no_counterexample | inconclusive
- **Details**: 1–3 sentences. If `no_counterexample`, why — was the formula actually correct here, or were preconditions unviolatable?

## Counterexamples found

If `outcome: counterexample_found`, present each counterexample as:

### Counterexample 1

- **Description**: plain-language description (one sentence).
- **Parameters**:
  | Task | C | T | D | … |
  |---|---|---|---|---|
  | τ₁ | … | … | … | … |
  | τ₂ | … | … | … | … |
- **Paper's result**: what the paper's formula/method gives.
- **Correct result**: what the correct value is (independently computed).
- **Discrepancy**: how they differ; whether the paper's bound is unsafe (under) or merely suboptimal (over).
- **Preconditions verified**: for each precondition listed above, how it was checked.
- **Verification method**: simulation / exact computation / exhaustive search / value iteration / etc.
- **Script**: filename of the Python script saved to disk.

## Conclusion

1–3 sentences. The bottom line: does the claim hold, does it fail, or is the investigation inconclusive? If `no_counterexample` despite serious audit concerns, classify them as expository (not falsifiable) and recommend the author tighten the *proof*, not the *result*.

## Recommended next step

- If `counterexample_found`: recommend `stress-test-defense` to check whether any precondition was missed, then `writeup-finding`.
- If `no_counterexample`: recommend rewriting the proof to close the audit's gaps. The result is probably correct; the *proof* is not.
- If `inconclusive`: state what would resolve it — a more elaborate construction, a different model assumption, retrieval of an external appendix.
```

## Common pitfalls (re-read before reporting a counterexample)

- The counterexample violates one of the theorem's preconditions. Re-check **every** precondition before claiming a break.
- Arithmetic done in your head, not in Python. Re-run the script.
- Confusing the paper's notation with your own — re-read the definitions carefully.
- Giving up after one failed attempt. Try all attack surfaces from the audit before reporting `no_counterexample`.
- Assuming a tie-breaking rule, execution order, or scheduling decision not specified by the model.
- For probabilistic claims: insufficient sample size. Use exact computation or very large N with confidence intervals.
- For scheduling claims: forgetting job releases at hyperperiod boundaries, confusing deadline models (implicit / constrained / arbitrary), ignoring self-suspensions.
- For DAG / parallel-tasks claims: ignoring topological ordering constraints on ready-job sets.
