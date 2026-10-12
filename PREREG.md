# Pre-registration (v1, committed before any of these experiments were run)

Scope: simulator-only checks. Nothing here concerns real deployed systems.
CIs are 95% normal-approximation (mean ± 1.96·sd/√n) over seeds. A claim PASSES only if its threshold holds
at the CI bound named below. Each result is reported as PASS, FAIL or INCONCLUSIVE, whichever it turns out to be.

## E-P1: shared bounded authority vs. gain superposition (fleet.py, model `p1`)
Setup: m ∈ {1..5} delayed integral load reducers, each tuned alone to ρ_i = 0.6. Independent: gains add.
CONCERTO P1: a single budget, Σρ ≤ 0.5.
- H1a: independent is unstable (growth rate > 0) for every m ≥ 2. PASS if true for all m ≥ 2.
- H1b: P1 is stable for every m and its settling time varies by less than 25% across m.
- H1c (cost of P1): at m = 1, P1 settling time is no more than 1.5× independent.

## E-P3: Γ-gated ejection (pool.py), 30 seeds per cell
Pool of 50 hosts. Mean utilization u ∈ {0.6, 0.7, 0.8, 0.85, 0.9, 0.95}, spread uniform ±0.1. Faulty hosts: 1.
Policies: none, max_ejection_percent = 10%, minHealthPercent = 50%, Γ-gate (Γ_post < 1).
- H3a (prediction): for "none", predicted Γ ≥ 1 vs. realized cascade (more than 3 extra ejections) agrees
  in at least 80% of runs, pooled.
- H3b: Γ-gate goodput ≥ max_ejection_percent goodput minus 1 percentage point in every u cell (CI lower bound of the difference ≥ −1 pp).
- H3c: in at least one u cell, Γ-gate goodput beats both the max_ejection_percent and minHealthPercent policies (CI lower bound > 0).

## E-fleet: B1–B4 and ablations (fleet.py, model `fleet`), 20 seeds
Primary metric: attainment, the fraction of offered load admitted while the queue stays within the SLO.
Secondary metrics: cost (mean replicas), oscillation (sd of total shed in the 2nd half), replica changes.
- H-RQ3: B4 attainment ≥ the best baseline among B1–B3 (CI lower bound of the difference ≥ −1 pp), AND B4 cost ≤ 1.15× that baseline's cost.
- H-RQ4: each "less Pk" ablation is worse than B4 on the metric its channel targets, by more than CI overlap:
  P1 → oscillation, P2 → attainment, P4 → replica changes. P3 is not exercised in the fleet model and is reported via E-P3.
- H-RQ2: B2 (retuned) fixes oscillation (actuation) relative to B1, AND B2 attainment stays below B4 (observation coupling).
  This is the paper's own central prediction. Per the prior run, retuning the HPA target can escape the trap, so a FAIL is plausible and is reported if it happens.

## E-P4: frequency separation
Reported as part of E-fleet ("less P4"). The test is H-RQ4's P4 clause.
