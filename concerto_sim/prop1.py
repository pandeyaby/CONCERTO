"""Prop 1 check: x'(t) = -sum_i g_i x(t - tau_i). Euler DDE integration.
Finds the critical gain scale k* (gains g_i -> k g_i) at which the loop goes
unstable, by bisection on a measured growth rate, and reports sum(rho_i) at k*,
with rho_i = g_i*tau_i/(pi/2) (each controller's own delay margin fraction)."""
import math

def growth_rate(gains, taus, T=None, dt=None):
    tmax = max(taus)
    dt = dt or min(taus) / 200.0
    T = T or 60 * tmax
    lags = [max(1, round(t / dt)) for t in taus]
    n = int(T / dt); H = max(lags)
    x = [1.0] * (H + 1)  # constant history
    for _ in range(n):
        xd = x[-1] - dt * sum(g * x[-1 - L] for g, L in zip(gains, lags))
        x.append(xd)
    # envelope: max |x| over first vs last quarter windows
    q = len(x) // 4
    a = max(abs(v) for v in x[q:2 * q]) + 1e-300
    b = max(abs(v) for v in x[-q:]) + 1e-300
    return math.log(b / a) / (2 * q * dt)

def critical(gains, taus, iters=30):
    lo, hi = 0.0, 1.0
    while growth_rate([hi * g for g in gains], taus) < 0:
        hi *= 2
    for _ in range(iters):
        mid = (lo + hi) / 2
        if growth_rate([mid * g for g in gains], taus) < 0: lo = mid
        else: hi = mid
    k = (lo + hi) / 2
    rho = sum(k * g * t / (math.pi / 2) for g, t in zip(gains, taus))
    return k, rho

CASES = [
    ("single", [1.0], [1.0]),
    ("2 equal gains, equal delays", [1.0, 1.0], [1.0, 1.0]),
    ("3 equal, equal delays", [1.0, 1.0, 1.0], [1.0, 1.0, 1.0]),
    ("2 equal rho, delays 1:2", [1.0, 0.5], [1.0, 2.0]),
    ("2 equal rho, delays 1:10", [1.0, 0.1], [1.0, 10.0]),
    ("2 equal rho, delays 1:100 (shedder vs autoscaler)", [1.0, 0.01], [1.0, 100.0]),
    ("2 equal gains, delays 1:10", [1.0, 1.0], [1.0, 10.0]),
]

def run():
    out = []
    for name, g, t in CASES:
        k, rho = critical(g, t)
        out.append({"case": name, "gains": g, "taus": t, "k_crit": round(k, 4),
                    "sum_rho_at_instability": round(rho, 3)})
    return out
