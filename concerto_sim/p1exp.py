"""E-P1: m delayed proportional controllers, each with rho=0.6 alone; independent vs. P1 budget."""
import math
from .arbiter import allocate

def settle(gains, tau=1.0, T=80.0, dt=0.005, tol=0.05):
    L = round(tau / dt); x = [1.0] * (L + 1); last = 0.0; big = False
    for k in range(int(T / dt)):
        x.append(x[-1] - dt * sum(gains) * x[-1 - L])
        if abs(x[-1]) > tol: last = k * dt
        if abs(x[-1]) > 1e6: big = True; break
    q = len(x) // 4
    grow = math.log((max(abs(v) for v in x[-q:]) + 1e-300) / (max(abs(v) for v in x[q:2*q]) + 1e-300))
    return {"settle_s": None if (big or grow > 0) else round(last, 2), "growing": big or grow > 0}

def run(rho=0.6, tau=1.0):
    out = []
    for m in range(1, 6):
        g = rho * (math.pi / 2) / tau
        ind = settle([g] * m, tau)
        alloc = allocate([rho] * m)
        p1 = settle([a * (math.pi / 2) / tau for a in alloc], tau)
        out.append({"m": m, "sum_rho_independent": round(rho * m, 2), "independent": ind,
                    "sum_rho_p1": round(sum(alloc), 2), "p1": p1})
    return out
