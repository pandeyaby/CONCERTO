"""Smoke CLI: python -m concerto_sim [--json]. Writes results/ledger.json."""
import json, sys, os
from . import prop1, prop2, detune, __version__

def main():
    res = {"version": __version__, "prop1": prop1.run(), "prop2": prop2.run(),
           "detune": detune.run(),
           "does_not_claim": ["behavior of any real deployed system",
                              "that the models are faithful to Kubernetes/Envoy",
                              "anything about CONCERTO's performance (not implemented yet)"]}
    os.makedirs("results", exist_ok=True)
    with open("results/ledger.json", "w") as f: json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1) if "--json" in sys.argv else "SMOKE OK -> results/ledger.json")

if __name__ == "__main__": main()
