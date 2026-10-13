#!/usr/bin/env python3
"""Evaluate PREREG v3 under BOTH gap rules.

Original (primary): phase2>=470 and max_sample_gap_s<=10 (P3: phase2>=170, n>=1000).
Relaxed (secondary): phase2>=470 and gap<=600 and rep_n>=60 and final_replicas set
  (introduced mid-campaign after kubectl API stalls); trials accepted only under
  this rule are tagged sampling=degraded.

Emits dual_verdicts.json and prints a summary. Does not mutate results_campaign.json.
"""
from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import analyze

RUNS = Path(__file__).resolve().parent / "runs"


def analyze_all():
    out = {}
    for d in sorted(RUNS.iterdir()):
        if not d.is_dir():
            continue
        name = d.name
        if not any(name.startswith(p) for p in ("ac_", "tt_", "p1_", "p3_")):
            continue
        if not (d / "v2.bin").exists() or (d / "v2.bin").stat().st_size == 0:
            continue
        try:
            a = analyze(str(d))
        except Exception as e:
            out[name] = {"error": str(e)}
            continue
        rep_n = sum(
            1
            for l in open(d / "replicas.csv")
            if l.strip().split(",")[-1].isdigit()
        )
        a["rep_n"] = rep_n
        if name.startswith("p3_"):
            orig = a["phase2_duration_s"] >= 170 and a.get("n", 0) >= 1000
            relaxed = orig
        else:
            orig = a["phase2_duration_s"] >= 470 and a["max_sample_gap_s"] <= 10
            relaxed = (
                a["phase2_duration_s"] >= 470
                and a["max_sample_gap_s"] <= 600
                and rep_n >= 60
                and a["final_replicas"] is not None
            )
        a["valid_original"] = bool(orig)
        a["valid_relaxed"] = bool(relaxed)
        out[name] = a
    return out


def arm(R, prefix, rule):
    key = "valid_original" if rule == "original" else "valid_relaxed"
    return [v for k, v in sorted(R.items()) if k.startswith(prefix) and v.get(key)]


def mean(xs, key):
    return st.mean(v[key] for v in xs) if xs else float("nan")


def V(b):
    return "PASS" if b else "FAIL"


def eval_rule(R, rule):
    v = {}
    trap, rev = arm(R, "ac_trap_", rule), arm(R, "ac_reverse_", rule)
    if len(trap) >= 1 and len(rev) >= 1:
        v["AC1"] = V(all(x["final_replicas"] <= 2 and x["attain"] <= 0.45 for x in trap))
        v["AC2"] = V(all(x["final_replicas"] >= 5 and x["attain"] >= 0.85 for x in rev))
        v["AC3"] = V(mean(rev, "attain") - mean(trap, "attain") >= 0.3)
        v["AC_n"] = f"{len(trap)}/{len(rev)}"
        v["AC_means"] = {
            "trap": round(mean(trap, "attain"), 4),
            "reverse": round(mean(rev, "attain"), 4),
        }
        v["AC_incomplete"] = len(trap) < 3 or len(rev) < 3
    else:
        v["AC"] = "INCONCLUSIVE (missing trials)"

    safe, indep = arm(R, "tt_safe_", rule), arm(R, "tt_indep_", rule)
    if safe and indep:
        v["TT1"] = V(all(x["attain"] <= 0.55 for x in indep))
        v["TT2"] = V(mean(safe, "attain") - mean(indep, "attain") >= 0.25)
        v["TT3"] = V(all(x["final_replicas"] >= 4 for x in safe))
        v["TT_n"] = f"{len(safe)}/{len(indep)}"
        v["TT_means"] = {
            "safe": round(mean(safe, "attain"), 4),
            "indep": round(mean(indep, "attain"), 4),
        }
        v["TT_incomplete"] = len(safe) < 3 or len(indep) < 3
    else:
        v["TT"] = "INCONCLUSIVE (missing trials)"

    p1 = arm(R, "p1_budget_", rule)
    if p1 and indep and safe:
        v["P1a"] = V(mean(p1, "attain") >= mean(indep, "attain") - 0.05)
        v["P1b"] = V(mean(p1, "final_replicas") >= mean(indep, "final_replicas"))
        v["P1c"] = V(mean(p1, "attain") >= mean(safe, "attain") - 0.15)
        v["P1_n"] = len(p1)
        v["P1_mean_attain"] = round(mean(p1, "attain"), 4)
        v["P1_incomplete"] = len(p1) < 3
    else:
        v["P1"] = "INCONCLUSIVE (missing trials)"

    none, maxej, minh, gamma = (
        arm(R, "p3_none_", rule),
        arm(R, "p3_maxej10_", rule),
        arm(R, "p3_minhealth50_", rule),
        arm(R, "p3_gamma_", rule),
    )
    if none and maxej and minh and gamma:
        v["P3a"] = V(
            mean(none, "attain") <= 0.85
            or (mean(gamma, "attain") - mean(none, "attain") >= 0.05)
        )
        v["P3b"] = V(abs(mean(gamma, "attain") - mean(maxej, "attain")) <= 0.05)
        v["P3c"] = V(mean(gamma, "attain") >= mean(minh, "attain") - 0.05)
        v["P3_means"] = {
            k: round(mean(vs, "attain"), 4)
            for k, vs in [
                ("none", none),
                ("maxej10", maxej),
                ("minhealth50", minh),
                ("gamma", gamma),
            ]
        }
        v["P3_incomplete"] = any(len(x) < 3 for x in (none, maxej, minh, gamma))
    else:
        v["P3"] = "INCONCLUSIVE (missing trials)"
    return v


def main():
    R = analyze_all()
    affected = {
        k: {
            "max_sample_gap_s": v.get("max_sample_gap_s"),
            "valid_original": v.get("valid_original"),
            "valid_relaxed": v.get("valid_relaxed"),
            "attain": v.get("attain"),
            "final_replicas": v.get("final_replicas"),
        }
        for k, v in R.items()
        if v.get("valid_relaxed") and not v.get("valid_original")
    }
    invalid_both = {
        k: {
            "max_sample_gap_s": v.get("max_sample_gap_s"),
            "attain": v.get("attain"),
            "phase2_duration_s": v.get("phase2_duration_s"),
        }
        for k, v in R.items()
        if not v.get("valid_original") and not v.get("valid_relaxed") and "error" not in v
    }
    payload = {
        "gap_rules": {
            "original_primary": "HPA arms: phase2>=470 AND max_sample_gap_s<=10; P3: phase2>=170 AND n>=1000",
            "relaxed_secondary": "HPA arms: phase2>=470 AND gap<=600 AND rep_n>=60 AND final_replicas set (mid-campaign; kubectl timeout stalls)",
        },
        "trials": R,
        "affected_relaxed_only": affected,
        "invalid_under_both": invalid_both,
        "verdicts_original": eval_rule(R, "original"),
        "verdicts_relaxed": eval_rule(R, "relaxed"),
    }
    out = Path(__file__).resolve().parent / "dual_verdicts.json"
    json.dump(payload, open(out, "w"), indent=2)
    print(json.dumps({
        "n_trials": len(R),
        "relaxed_only": sorted(affected),
        "invalid_both": sorted(invalid_both),
        "verdicts_original": payload["verdicts_original"],
        "verdicts_relaxed": payload["verdicts_relaxed"],
    }, indent=2))


if __name__ == "__main__":
    main()
