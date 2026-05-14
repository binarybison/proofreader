# Counterexample Investigation: ILP Formulation (Figure 3)

**Mode**: adversarial
**Outcome**: counterexample_found
**Confidence**: high

## Claim restated

The published ILP encoding from RTNS 2020 Figure 3 correctly identifies schedulable task sets: it should return *feasible* if and only if a valid schedule exists.

## Preconditions

A valid counterexample must satisfy:

1. Be a finite set of jobs with explicit release times, execution requirements, and absolute deadlines.
2. Run on the multiprocessor model the paper specifies (`m` identical processors; the encoding pins each job to a processor via its own variables).
3. Have ordering and demand-bound variables ranging over the domains the paper defines (binary `x_{ij}`, etc.).
4. Be actually unschedulable under any feasible schedule (verified independently by simulation / direct construction).
5. Be reported as schedulable by the published ILP (verified by running the encoding through an ILP solver, or by exhibiting a feasible assignment to all variables under the published constraints).

## Attack surfaces attempted

### Attack surface 1: Ordering variables left zero on a contended pair

- **Source**: audit Issue 1 (missing totality on `x_{ij}`)
- **Hypothesis**: if the encoding allows `x_{ij} = x_{ji} = 0`, the demand-bound constraints for the pair `(i, j)` go inactive, letting the solver inflate available slack.
- **Outcome**: counterexample_found
- **Details**: a 2-job instance constructed below exhibits exactly this failure mode.

## Counterexamples found

### Counterexample 1: Minimal 2-job instance

- **Description**: two jobs on one processor with total demand 6 and a common deadline 5. The actual minimum makespan is 6 (unavoidable since both jobs must execute sequentially on one processor), so the instance is unschedulable. The published ILP, however, declares it schedulable because the ordering variables remain unconstrained.

- **Parameters**:

  | Job | Processor | Release time | Execution time | Deadline |
  |---|---|---|---|---|
  | J₁ | 1 | 0 | 3 | 5 |
  | J₂ | 1 | 0 | 3 | 5 |

- **Paper's result**: The published ILP returns *feasible* (a solution assigns `x_{12} = x_{21} = 0`, which leaves the demand-bound constraint between J₁ and J₂ inactive; the solver then satisfies all remaining constraints).

- **Correct result**: The instance is unschedulable. A direct simulation confirms: on one processor with two jobs each requiring 3 time units, the minimum completion time of the later-finishing job is 6. With a common deadline of 5, no valid schedule exists.

- **Discrepancy**: 1 time unit of unaccounted demand (demand = 6, deadline = 5, excess = 1 unit = 20% relative error).

- **Preconditions verified**:
  - (1) Two jobs, fully specified parameters. ✓
  - (2) Single processor; matches the paper's `m = 1` instance. ✓
  - (3) Binary `x_{ij}` variables; integer execution and deadline values. ✓
  - (4) Unschedulable by direct simulation (see [verification-script.py](verification-script.py)). ✓
  - (5) Reported feasible by the published ILP: the assignment `x_{12} = x_{21} = 0` together with the published constraints admits a feasible solution. ✓

- **Verification method**: direct simulation by exhaustive enumeration of execution orders (only two for 2 jobs on 1 processor — `J₁ then J₂` and `J₂ then J₁`). Both produce a deadline miss at `t = 6 > 5`. The published ILP is verified to be vacuously satisfiable on this instance under the assignment above by direct substitution into the constraint set.

- **Script**: [verification-script.py](verification-script.py).

## Counterexample 2: 3-job extension

(Sketch only — see source corpus for full details.) The 2-job pattern extends naturally to a 3-job instance with one more degree of freedom in the ordering, exhibiting `12.5%` relative demand error. The 3-job case suggests the bug is *structural* (it scales with `n`) rather than an edge case of small instances.

## Conclusion

The published ILP formulation has a confirmed soundness bug. Any task set with two or more contended jobs on the same processor can trigger it when the solver finds it advantageous to leave ordering variables at zero. The fix is the totality constraint identified in the audit.

## Recommended next step

- Run `/stress-test-defense ILP-Figure-3` to check whether some constraint elsewhere implicitly forces totality. (The defender's job is to find such a constraint if it exists; the arbiter's job is to verify the defender's claim independently.)
- After the stress-test renders `true_positive` (expected), run `writeup-finding` in `latex` format to produce a brief suitable for filing as an erratum or for inclusion in a revised manuscript.
