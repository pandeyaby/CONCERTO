"""Prop 2 with the direct negative path included.
Queue fluid model: q' = lambda*(1-s) - mu, q>=0.  Shedder (fast): s' = gF*(q-q_ref)/q_ref,
clipped [0, smax]. Autoscaler (slow): every period P reads a demand signal averaged over
the last period, desired = ceil(signal/(c*target)); downscale uses the max recommendation
in the last W seconds (K8s-style stabilization); new replicas arrive after start delay D.
Masked: signal = admitted rate lambda*(1-s). P2 (reconstructed): signal = lambda.
Also reports the linearized masked system's eigenvalues."""
import math, random

def linear_eigs(gF, gS):
    # states (x, dmu): x' = -gF x - dmu ; dmu' = gS(-gF x - dmu)
    a, b, c, d = -gF, -1.0, -gS * gF, -gS
    tr, det = a + d, a * d - b * c
    disc = tr * tr - 4 * det
    r = math.sqrt(abs(disc))
    return ((tr + r) / 2, (tr - r) / 2) if disc >= 0 else (complex(tr / 2, r / 2), complex(tr / 2, -r / 2))

def simulate(mode="masked", gF=2.0, W=300.0, D=30.0, P=15.0, target=0.7, c=10.0,
             lam0=80.0, lam1=120.0, step_t=600.0, T=7200.0, dt=0.05, smax=0.9,
             q_ref=20.0, noise=0.0, seed=0, shed_util=None):
    rng = random.Random(seed)
    reps = math.ceil(lam0 / (c * target)); q = 0.0; s = 0.0
    pending = []; recs = []; acc = 0.0; nacc = 0; t = 0.0; nextP = P
    trace = []
    while t < T:
        lam = (lam1 if t >= step_t else lam0) * (1 + noise * rng.gauss(0, 1))
        mu = reps * c
        adm = lam * (1 - s)
        q = max(0.0, q + dt * (adm - mu))
        err = (q - q_ref) / q_ref if shed_util is None else (lam * (1 - s) / mu - shed_util)
        s = min(smax, max(0.0, s + dt * gF * err))
        acc += adm if mode == "masked" else lam; nacc += 1
        while pending and pending[0][0] <= t:
            reps = pending.pop(0)[1]
        if t >= nextP:
            sig = acc / nacc; acc = 0.0; nacc = 0; nextP += P
            want = max(1, math.ceil(sig / (c * target)))
            recs.append((t, want)); recs = [(tt, w) for tt, w in recs if tt >= t - W]
            stab = max(w for _, w in recs)
            goal = want if want > reps else min(reps, stab)
            if goal != reps and not any(g == goal for _, g in pending):
                pending.append((t + (D if goal > reps else 0.0), goal))
        trace.append((t, reps, s, q)); t += dt
    tail = [r for r in trace if r[0] > T / 2]
    R = [r[1] for r in tail]; S = [r[2] for r in tail]
    return {"mode": mode, "gF": gF, "W": W, "shed_util": shed_util, "target": target, "final_replicas": R[-1],
            "replicas_min_max_2nd_half": [min(R), max(R)],
            "mean_shed_2nd_half": round(sum(S) / len(S), 4),
            "mean_queue_2nd_half": round(sum(r[3] for r in tail) / len(tail), 2),
            "needed_replicas_for_lam1": math.ceil(lam1 / (c * target))}

def run():
    out = {"linear_eigs": {f"gF={gF},gS={gS}": [str(e) for e in linear_eigs(gF, gS)]
                           for gF in (0.5, 2.0) for gS in (0.01, 0.1)}}
    out["step"] = [simulate(m) for m in ("masked", "p2")]
    out["noisy_step"] = [simulate(m, noise=0.1, seed=1) for m in ("masked", "p2")]
    # shedder trips on utilization BELOW the HPA target (latency rises before saturation)
    out["shed_below_target"] = [simulate(m, shed_util=u) for u in (0.6, 0.69, 0.75) for m in ("masked", "p2")]
    return out
