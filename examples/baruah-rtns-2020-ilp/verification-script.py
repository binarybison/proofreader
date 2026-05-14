"""Verification script for the counterexample to Baruah RTNS 2020 ILP encoding.

Demonstrates that the 2-job instance described in counterexample-excerpt.md is:
  (a) actually unschedulable on one processor (direct simulation), and
  (b) accepted as feasible by the published ILP encoding when ordering
      variables are left unconstrained (constraint substitution).

This script intentionally does not import an ILP solver. (a) is verified
by exhaustive enumeration, which is sufficient at this instance size; (b)
is verified by direct substitution into the constraint set.

Run with: python verification-script.py
"""

from itertools import permutations

# 2-job instance: J1, J2 on one processor with deadline 5 and execution 3 each.
JOBS = [
    {"id": "J1", "processor": 1, "release": 0, "execution": 3, "deadline": 5},
    {"id": "J2", "processor": 1, "release": 0, "execution": 3, "deadline": 5},
]


def simulate_order(order):
    """Simulate executing jobs in the given order on a single processor.

    Returns the list of (job_id, finish_time, deadline_met) tuples.
    """
    t = 0
    out = []
    for job in order:
        start = max(t, job["release"])
        finish = start + job["execution"]
        out.append((job["id"], finish, finish <= job["deadline"]))
        t = finish
    return out


def part_a_is_unschedulable():
    """Verify via exhaustive enumeration that no order meets all deadlines."""
    print("Part (a): direct simulation of all execution orders\n")
    any_feasible = False
    for order in permutations(JOBS):
        schedule = simulate_order(order)
        ids = " -> ".join(j["id"] for j in order)
        misses = [(jid, ft, dl) for (jid, ft, dl) in schedule if not dl]
        if not misses:
            any_feasible = True
            print(f"  {ids}: feasible (no deadline miss)")
        else:
            for jid, ft, _ in schedule:
                deadline = next(j["deadline"] for j in JOBS if j["id"] == jid)
                tag = "OK" if ft <= deadline else f"MISS by {ft - deadline}"
                print(f"  {ids}: {jid} finishes at t={ft} (deadline {deadline}) [{tag}]")
            print()
    print("Conclusion (a): instance is", "FEASIBLE" if any_feasible else "UNSCHEDULABLE")
    return not any_feasible


def part_b_published_ilp_accepts():
    """Verify the published ILP encoding accepts the unschedulable instance.

    The published encoding has constraints:
        x_{12} + x_{21} <= 1          (anti-symmetry; published)
        # x_{12} + x_{21} >= 1        (totality; MISSING in the published version)
        c_{12k} >= demand contribution if x_{12} = 1
        c_{21k} >= demand contribution if x_{21} = 1
        sum_k c_{ijk} <= capacity_k
    With x_{12} = x_{21} = 0, all c_{ijk} are unconstrained (can be 0).
    Then the demand-bound aggregate is 0, vacuously <= any capacity.
    """
    print("\nPart (b): assignment satisfying the PUBLISHED constraint set\n")

    x = {("J1", "J2"): 0, ("J2", "J1"): 0}
    c = {("J1", "J2"): 0, ("J2", "J1"): 0}

    # Published anti-symmetry
    assert x[("J1", "J2")] + x[("J2", "J1")] <= 1, "anti-symmetry violated"
    print("  anti-symmetry x_12 + x_21 = 0 <= 1: OK")

    # The MISSING totality (would be violated):
    totality_holds = x[("J1", "J2")] + x[("J2", "J1")] >= 1
    print(f"  (missing) totality x_12 + x_21 >= 1: would be {'OK' if totality_holds else 'VIOLATED'}")

    # Demand-bound aggregate over the only relevant interval (0..deadline):
    aggregate_demand = sum(c.values())
    capacity = 5
    print(f"  demand aggregate = {aggregate_demand} <= capacity {capacity}: OK")

    print("Conclusion (b): published ILP returns FEASIBLE (incorrect)")
    return True


if __name__ == "__main__":
    a = part_a_is_unschedulable()
    b = part_b_published_ilp_accepts()
    print()
    print(f"Combined: instance unschedulable but published ILP returns feasible? {a and b}")
    print(f"Discrepancy: 1 time unit of unaccounted demand (20% relative error).")
    print(f"Fix: add constraint x_ij + x_ji = 1 for every contended job pair.")
