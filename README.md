# CONCERTO

Evaluation artifact for *Too Many Hands on the Throttle: Arbitrating Overlapping
Reliability Controls in Service Fleets* (draft in `paper/`).

- `audit/mechanisms.csv`: Step 0 configuration-surface audit. Doc versions are pinned and every cell has a source URL.
- `concerto_sim/`: thin simulator. Stdlib only and deterministic. Smoke run: `python3 -m concerto_sim [--json]`.
- `results/ledger.json`: results ledger written by the smoke run.
- `testbed/`: k3s + Envoy + HPA harness. RQ1 (PREREG v2) and campaign arms AC / two-tier / P1 / P3 (PREREG v3).
  - Bring-up: `./testbed/setup.sh`
  - RQ1 trial: `./testbed/trial.sh <R> <label>`
  - Campaign: `./testbed/run_campaign.sh` then `python3 testbed/dual_verdicts.py`
  - Results: `CAMPAIGN_RESULTS.md` (original gap rule primary; relaxed secondary)

## Does not claim
- Anything about real deployed systems beyond the single-node testbed described in PREREG.md.
- That the fluid or HPA models are faithful to Kubernetes or Envoy.
- That the adaptive-concurrency arm exercises gradient dynamics (concurrency is pinned; see PREREG v3).
