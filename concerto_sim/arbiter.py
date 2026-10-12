"""CONCERTO arbiter: the four principles as pure functions used by the models.
P1 allocate(): one budget B on summed margin fraction; requests are scaled proportionally.
P2 reconstruct(): the provisioning signal is admitted + shed (= offered) load.
P3 gamma(): projected cascade gain of one ejection, plus an admission gate.
P4 Band: an EMA low-pass. The slow band feeds the provisioner; fast actuators keep the raw signal."""
import math

def allocate(rhos, B=0.5):
    s = sum(rhos)
    k = 1.0 if s <= B else B / s
    return [r * k for r in rhos]

def reconstruct(admitted, shed):
    return admitted + shed

def gamma(loads, caps, alive, j):
    """Expected number of survivors pushed over capacity if host j is ejected and its load is spread evenly."""
    surv = [i for i in alive if i != j]
    if not surv: return float("inf")
    share = loads[j] / len(surv)
    return sum(1 for i in surv if loads[i] <= caps[i] < loads[i] + share)

class Band:
    def __init__(self, tau, dt):
        self.a = dt / (tau + dt); self.y = None
    def __call__(self, x):
        self.y = x if self.y is None else self.y + self.a * (x - self.y)
        return self.y
