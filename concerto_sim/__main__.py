"""Smoke CLI: python -m concerto_sim [--json]. Writes results/ledger.json."""
import json, sys, os
from . import prop1, prop2, detune, p1exp, pool, fleet, __version__

def main():
    res = {"version": __version__, "prop1": prop1.run(), "prop2": prop2.run(),
           "detune": detune.run(), "e_p1": p1exp.run(), "e_p3": pool.run(), "e_fleet": fleet.run(),
           "prereg": "PREREG.md v1; verdicts in RESULTS.md",
           "does_not_claim": ["behavior of any real deployed system",
                              "that the models are faithful to Kubernetes/Envoy",
                              "CONCERTO performance outside these toy models (the arbiter exists only in the simulator)",
                              "that 60%-trip shedders below a 70% HPA target are common (a modeling assumption, unaudited)",
                              "that the pool model's goodput (overloaded hosts serve at capacity) matches real overload behaviour",
                              "anything about P3 inside the fleet model (not exercised there)",
                              "statistical significance beyond the stated normal-approx 95% CIs over 20-30 seeds"]}
    os.makedirs("results", exist_ok=True)
    with open("results/ledger.json", "w") as f: json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1) if "--json" in sys.argv else "SMOKE OK -> results/ledger.json")

if __name__ == "__main__": main()
