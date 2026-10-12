# CONCERTO

Evaluation artifact for *Too Many Hands on the Throttle: Arbitrating Overlapping
Reliability Controls in Service Fleets* (draft in `paper/`).

- `audit/mechanisms.csv`: Step 0 configuration-surface audit. Doc versions are pinned and every cell has a source URL.
- `concerto_sim/`: thin simulator. Stdlib only and deterministic. Smoke run: `python3 -m concerto_sim [--json]`.
- `results/ledger.json`: results ledger written by the smoke run.

## Does not claim
- Anything about real deployed systems. These are model checks of the paper's propositions.
- That the fluid or HPA models are faithful to Kubernetes or Envoy.
- Anything about CONCERTO's own performance. The arbiter is not implemented.
