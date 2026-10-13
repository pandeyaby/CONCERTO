#!/usr/bin/env python3
"""Evaluate PREREG v3 hypotheses against results_campaign.json."""
from __future__ import annotations

import json
import statistics as st
import sys

R = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "results_campaign.json"))


def arm(prefix: str):
    out = []
    for k, v in sorted(R.items()):
        if k.startswith(prefix) and "error" not in v:
            out.append(v)
    return out


def mean(xs, key):
    return st.mean(v[key] for v in xs)


def V(b):
    return "PASS" if b else "FAIL"


verdicts = {}

# E-AC
trap, rev = arm("ac_trap_"), arm("ac_reverse_")
if trap and rev:
    ac1 = all(v["final_replicas"] <= 2 and v["attain"] <= 0.45 for v in trap)
    ac2 = all(v["final_replicas"] >= 5 and v["attain"] >= 0.85 for v in rev)
    ac3 = mean(rev, "attain") - mean(trap, "attain") >= 0.3
    verdicts["AC1"] = V(ac1)
    verdicts["AC2"] = V(ac2)
    verdicts["AC3"] = V(ac3)
    verdicts["AC_n"] = f"{len(trap)}/{len(rev)}"
    verdicts["AC_means"] = {
        "trap": round(mean(trap, "attain"), 4),
        "reverse": round(mean(rev, "attain"), 4),
    }
else:
    verdicts["AC"] = "INCONCLUSIVE (missing trials)"

# E-two-tier
safe, indep = arm("tt_safe_"), arm("tt_indep_")
if safe and indep:
    tt1 = all(v["attain"] <= 0.55 for v in indep)
    tt2 = mean(safe, "attain") - mean(indep, "attain") >= 0.25
    tt3 = all(v["final_replicas"] >= 4 for v in safe)
    verdicts["TT1"] = V(tt1)
    verdicts["TT2"] = V(tt2)
    verdicts["TT3"] = V(tt3)
    verdicts["TT_n"] = f"{len(safe)}/{len(indep)}"
    verdicts["TT_means"] = {
        "safe": round(mean(safe, "attain"), 4),
        "indep": round(mean(indep, "attain"), 4),
    }
else:
    verdicts["TT"] = "INCONCLUSIVE (missing trials)"

# E-P1
p1 = arm("p1_budget_")
if p1 and indep and safe:
    p1a = mean(p1, "attain") >= mean(indep, "attain") - 0.05
    p1b = mean(p1, "final_replicas") >= mean(indep, "final_replicas")
    p1c = abs(mean(p1, "attain") - mean(safe, "attain")) <= 0.15 or mean(p1, "attain") >= mean(safe, "attain") - 0.15
    verdicts["P1a"] = V(p1a)
    verdicts["P1b"] = V(p1b)
    verdicts["P1c"] = V(p1c)
    verdicts["P1_n"] = len(p1)
    verdicts["P1_mean_attain"] = round(mean(p1, "attain"), 4)
else:
    verdicts["P1"] = "INCONCLUSIVE (missing trials)"

# E-P3
none, maxej, minh, gamma = arm("p3_none_"), arm("p3_maxej10_"), arm("p3_minhealth50_"), arm("p3_gamma_")
if none and maxej and minh and gamma:
    p3a = mean(none, "attain") <= 0.85 or (mean(gamma, "attain") - mean(none, "attain") >= 0.05)
    p3b = abs(mean(gamma, "attain") - mean(maxej, "attain")) <= 0.05
    p3c = mean(gamma, "attain") >= mean(minh, "attain") - 0.05
    verdicts["P3a"] = V(p3a)
    verdicts["P3b"] = V(p3b)
    verdicts["P3c"] = V(p3c)
    verdicts["P3_means"] = {
        k: round(mean(vs, "attain"), 4)
        for k, vs in [("none", none), ("maxej10", maxej), ("minhealth50", minh), ("gamma", gamma)]
    }
else:
    verdicts["P3"] = "INCONCLUSIVE (missing trials)"

print(json.dumps(verdicts, indent=2))
json.dump(verdicts, open("verdicts_v3.json", "w"), indent=2)
