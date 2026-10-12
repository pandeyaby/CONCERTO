"""E-fleet: an autoscaler plus two load reducers (shedder s1 and concurrency limiter s2), both integral
controllers on delayed utilization (delay tau), both tripping at 60% utilization (below the HPA target of 70%:
this is the observation-coupling trap from the earlier run; it is a modeling assumption, not an audited default).
Load: step 80->120 at t=600, seeded bursts (+40% for 20 s, mean gap 150 s), 5% gaussian noise.
Configurations: B1 defaults, B2 retuned, B3 strict precedence, B4 CONCERTO, B4 less P1/P2/P4."""
import math, random
from .arbiter import allocate, reconstruct, Band
from .stats import ci, diff_ci

def run_one(cfg, seed, T=4800.0, dt=0.1, c=10.0, tau=3.0, D=30.0, P=15.0):
    rng = random.Random(seed)
    target, W, gmul = cfg.get("target", 0.7), cfg.get("W", 300.0), cfg.get("gmul", 1.0)
    p1, p2, p4, prec = cfg.get("p1"), cfg.get("p2"), cfg.get("p4"), cfg.get("prec")
    th = 0.6; g_alone = 0.6 * (math.pi / 2) / tau      # each limiter alone: rho=0.6 at k=1
    reps = math.ceil(80 / (c * target)); s1 = s2 = 0.0; q = 0.0
    hist = [0.0] * (round(tau / dt) + 1); pending = []; recs = []; acc = n = 0
    band = Band(120.0, P); nextP = P; burst_end = -1; next_burst = rng.expovariate(1 / 150)
    off = adm_ok = 0.0; S = []; R = []; changes = 0; slo_q = 50.0
    t = 0.0
    while t < T:
        if t >= next_burst: burst_end = t + 20; next_burst = t + rng.expovariate(1 / 150)
        lam = (120 if t >= 600 else 80) * (1.4 if t < burst_end else 1.0) * (1 + 0.05 * rng.gauss(0, 1))
        mu = reps * c; keep = (1 - s1) * (1 - s2); adm = lam * keep
        q = max(0.0, q + dt * (adm - mu))
        hist.append(adm / mu); ud = hist.pop(0) if len(hist) > round(tau / dt) + 1 else hist[0]
        e = ud - th; k = lam / mu                     # k = plant sensitivity du/ds
        g1 = g2 = g_alone * gmul
        if p1:                                         # P1: one budget across both reducers
            rhos = [g * k * tau / (math.pi / 2) for g in (g1, g2)]
            a = allocate(rhos, 0.5); g1, g2 = [r * (math.pi / 2) / (k * tau) for r in a]
        s1 = min(0.9, max(0.0, s1 + dt * g1 * e))
        if not (prec and s1 > 0): s2 = min(0.9, max(0.0, s2 + dt * g2 * e))
        else: s2 = max(0.0, s2 - dt * g2 * abs(e))     # lower priority yields
        sig = reconstruct(adm, lam - adm) if p2 else adm
        acc += sig; n += 1
        while pending and pending[0][0] <= t: reps = pending.pop(0)[1]; changes += 1
        if t >= nextP:
            nextP += P; m = acc / n; acc = n = 0
            if p4: m = band(m)
            want = max(1, math.ceil(m / (c * target)))
            recs = [(tt, w) for tt, w in recs + [(t, want)] if tt >= t - W]
            goal = want if want > reps else min(reps, max(w for _, w in recs))
            if prec and s1 > 0 and goal < reps: goal = reps   # protection has precedence: no scale-down while shedding
            if goal != reps and not any(gg == goal for _, gg in pending):
                pending.append((t + (D if goal > reps else 0.0), goal))
        if t > T / 4:
            off += lam * dt; adm_ok += adm * dt * (q <= slo_q)
            S.append(1 - keep); R.append(reps)
        t += dt
    ms = sum(S) / len(S)
    return {"attain": adm_ok / off, "cost": sum(R) / len(R),
            "osc": math.sqrt(sum((x - ms) ** 2 for x in S) / len(S)), "changes": changes}

CONFIGS = {
 "B1_defaults": {},
 "B2_retuned": {"gmul": 0.4, "target": 0.55},
 "B3_precedence": {"prec": True},
 "B4_concerto": {"p1": True, "p2": True, "p4": True},
 "B4_less_P1": {"p2": True, "p4": True},
 "B4_less_P2": {"p1": True, "p4": True},
 "B4_less_P4": {"p1": True, "p2": True},
}
def run(seeds=20):
    raw = {k: [run_one(v, s) for s in range(seeds)] for k, v in CONFIGS.items()}
    summ = {k: {mtr: ci([r[mtr] for r in rs]) for mtr in ("attain", "cost", "osc", "changes")} for k, rs in raw.items()}
    col = lambda k, m: [r[m] for r in raw[k]]
    best = max(("B1_defaults", "B2_retuned", "B3_precedence"), key=lambda k: summ[k]["attain"]["mean"])
    diffs = {"best_baseline": best,
             "B4_minus_best_attain": diff_ci(col("B4_concerto", "attain"), col(best, "attain")),
             "B4_cost_ratio_vs_best": round(summ["B4_concerto"]["cost"]["mean"] / summ[best]["cost"]["mean"], 3)}
    for abl, m in (("B4_less_P1", "osc"), ("B4_less_P2", "attain"), ("B4_less_P4", "changes")):
        diffs[f"{abl}_minus_B4_{m}"] = diff_ci(col(abl, m), col("B4_concerto", m))
    diffs["B2_minus_B1_osc"] = diff_ci(col("B2_retuned", "osc"), col("B1_defaults", "osc"))
    diffs["B2_minus_B4_attain"] = diff_ci(col("B2_retuned", "attain"), col("B4_concerto", "attain"))
    return {"summary": summ, "diffs": diffs}
