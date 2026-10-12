"""E-P3: ejection cascades in a 50-host pool. Overloaded (util>1) or faulty hosts look like outliers.
Each round: every alive host with util>1 or that is faulty is a candidate for ejection; the policy decides;
load from ejected hosts is spread evenly over the alive hosts. Goodput = served/offered, where a faulty
host serves 0 and an overloaded host serves its capacity."""
import random
from .arbiter import gamma
from .stats import ci, diff_ci

def run_one(u, policy, seed, N=50, faulty=1, rounds=60):
    rng = random.Random(seed)
    caps = [1.0] * N
    w = [max(0.05, u + rng.uniform(-0.1, 0.1)) for _ in range(N)]
    total = sum(w); bad = set(rng.sample(range(N), faulty))
    alive = set(range(N)); ej = 0
    def loads():
        tw = sum(w[i] for i in alive)
        return [total * w[i] / tw if i in alive else 0.0 for i in range(N)]
    L = loads()
    pred = gamma(L, caps, alive, next(iter(bad)))
    for _ in range(rounds):
        L = loads()
        cands = [i for i in sorted(alive) if i in bad or L[i] > caps[i]]
        if not cands: break
        acted = False
        for j in cands:
            if policy == "max_ejection_10pct" and (N - len(alive) + 1) > 0.1 * N: continue
            if policy == "min_health_50pct":
                healthy = sum(1 for i in alive if i not in bad and L[i] <= caps[i])
                if healthy < 0.5 * N: continue
            if policy == "gamma_gate" and gamma(L, caps, alive, j) >= 1 and j not in bad: continue
            if policy == "gamma_gate" and j in bad and gamma(L, caps, alive, j) >= 1:
                pass  # a faulty host serves nothing; ejecting it moves only load that was failing anyway
            alive.discard(j); ej += 1; acted = True; break
        if not acted: break
    L = loads()
    served = sum(0.0 if i in bad else min(L[i], caps[i]) for i in alive)
    return {"goodput": served / total, "extra_ejections": ej - len(bad & (set(range(N)) - alive)), "pred_gamma": pred}

POLICIES = ["none", "max_ejection_10pct", "min_health_50pct", "gamma_gate"]
def run(seeds=30):
    cells = []; agree = tot = 0
    for u in (0.6, 0.7, 0.8, 0.85, 0.9, 0.95):
        res = {p: [run_one(u, p, s) for s in range(seeds)] for p in POLICIES}
        for r in res["none"]:
            tot += 1; agree += ((r["pred_gamma"] >= 1) == (r["extra_ejections"] > 3))
        g = {p: [r["goodput"] for r in res[p]] for p in POLICIES}
        cells.append({"u": u,
            "goodput": {p: ci(g[p]) for p in POLICIES},
            "extra_ejections_mean": {p: sum(r["extra_ejections"] for r in res[p]) / seeds for p in POLICIES},
            "gate_minus_maxej": diff_ci(g["gamma_gate"], g["max_ejection_10pct"]),
            "gate_minus_minhealth": diff_ci(g["gamma_gate"], g["min_health_50pct"])})
    return {"cells": cells, "prediction_agreement": round(agree / tot, 3), "n": tot}
