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

# Pre-registration v2: testbed RQ1, threshold-ordering trap (committed before any testbed run)
Testbed: k3s v1.31.4 (single node, on the box, $0). App: a Python HTTP service with a fixed capacity of about
50 req/s per pod (4 workers × 80 ms sleep). Each pod has an Envoy sidecar with `local_ratelimit`, which acts as a
per-pod shedder: the token bucket refills R tokens/s and excess requests get a 429. HPA autoscaling/v2 scales on
the per-pod rate of 2xx responses at Envoy, read from Prometheus via prometheus-adapter. Target 35 req/s
per pod (0.7 of capacity). minReplicas 2, maxReplicas 8. Open-loop load (vegeta, constant rate):
50 req/s for 60 s, then 160 req/s for 480 s.
Conditions: TRAP R = 30 req/s per pod (trips at 0.6 < 0.7). REVERSE R = 40 req/s per pod (0.8 > 0.7). Trials: 3 each.
Metrics are measured over the last 240 s: attainment = 2xx/offered, final replicas, and mean replicas.
- T1 (trap reproduces): every TRAP trial ends with ≤ 2 replicas and attainment ≤ 0.45.
- T2 (reverse escapes): every REVERSE trial reaches ≥ 5 replicas and attainment ≥ 0.85.
- T3: the mean attainment gap between REVERSE and TRAP is ≥ 0.3.
Caveat fixed in advance: a token-bucket local rate limiter set per pod is a stand-in for a capacity-relative shedder.
Envoy adaptive concurrency is not tested here.

# Pre-registration v3: testbed campaign (P3, P1, AC trap, two-tier)
Committed before any v3 trial is run. Same box and stack as v2 (k3s v1.31.4, Envoy v1.31.4,
prometheus-adapter, vegeta). Unless noted, load profile matches v2: 50 req/s × 60 s, then 160 req/s × 480 s;
metrics over the final 240 s; HPA target 35 req/s per pod (0.7 of ~50 capacity), min 2 / max 8 replicas.
Each claim is PASS / FAIL / INCONCLUSIVE. Trials per arm: 3 unless noted.

## E-AC: adaptive-concurrency threshold-ordering trap
Addresses the v2 caveat. Sidecar shedder is Envoy `adaptive_concurrency` (rejects with 503) instead of
`local_ratelimit`. Gradient controller is pinned (`min_concurrency` = `max_concurrency_limit` = L) so the
filter is a fixed concurrency limiter on the AC rejection path — a stand-in for capacity-relative AC under
a known in-flight bound, not a test of the gradient controller's dynamics.
- TRAP: L = 2 (≈ 25 successful req/s per pod at 80 ms service time; 0.5 of capacity < 0.7 target).
- REVERSE: L = 6 (bound above app capacity; successful rate can exceed the 35 target).
- HPA metric unchanged: per-pod 2xx RPS (`envoy_ok_rps`). 503s do not count as success.
- AC1: every TRAP trial ends with ≤ 2 replicas and attainment ≤ 0.45.
- AC2: every REVERSE trial reaches ≥ 5 replicas and attainment ≥ 0.85.
- AC3: mean attainment gap REVERSE − TRAP ≥ 0.3.

## E-two-tier: independent edge + sidecar shedding
Two load reducers without a shared budget (actuation coupling at two tiers). Sidecar `local_ratelimit`
R_side = 40 (alone would escape the RQ1 trap). Edge Envoy also has `local_ratelimit` R_edge.
- TT-SAFE: R_edge = 200 (effectively off relative to 160 offered) — expect escape like REVERSE.
- TT-INDEP: R_edge = 80 (edge admits 80/s total; with 2 pods sidecar-capped at 40 each the plant is
  double-bounded). Expect attainment collapse and ≤ 3 final replicas (edge hides demand from HPA
  and/or oversheds relative to a single tier).
- TT1: every TT-INDEP trial has attainment ≤ 0.55.
- TT2: mean attainment TT-SAFE − TT-INDEP ≥ 0.25.
- TT3: every TT-SAFE trial reaches ≥ 4 replicas.

## E-P1: shared bounded authority on the two-tier plant
Same plant as E-two-tier. CONCERTO P1 stand-in: a single shared refill budget B = 100 token/s split
across edge and sidecar so ΣR = B (edge 50 + per-pod sidecar 25, with 2–8 pods the per-pod cap is a
soft outer bound; the governing knobs are the configured rates under the budget).
Compare to TT-INDEP (unbudgeted).
- P1a: P1 mean attainment ≥ TT-INDEP mean attainment − 5 pp.
- P1b: P1 mean final replicas ≥ TT-INDEP mean final replicas (P1 must not worsen the under-provisioning).
- P1c (cost of budgeting): P1 attainment is within 15 pp of TT-SAFE (budgeting may sacrifice some headroom).

## E-P3: topology-gated ejection on Envoy outlier detection
Pool: 9 healthy app pods + 1 always-503 fault pod (10 endpoints; HPA disabled). Edge Envoy outlier
detection (`consecutive_5xx: 3`, short ejection time). Offered load 200 req/s for 180 s (no warm-up).
Policies (3 trials each):
- none: `max_ejection_percent = 100`.
- maxej10: `max_ejection_percent = 10` (vendor fixed-fraction cap → 1 host at N=10).
- minhealth50: `max_ejection_percent = 50` (Istio-style half-pool stand-in on this Envoy surface).
- gamma: Γ-derived one-host admission cap — eject the faulty host only; refuse further ejections
  while projected Γ_post ≥ 1 under uniform redistribution. On this N=10 pool that is also
  `max_ejection_percent = 10`, so gamma and maxej10 coincide numerically; P3b is a consistency
  check, and the informative contrasts are vs none and minhealth50. (A dynamic wrapper that
  recomputes Γ online is future work; this arm is the static Γ-derived cap.)
Metrics: goodput = 2xx/offered over the full 180 s; ejected_hint from edge admin cluster dump.
- P3a: under "none", mean goodput ≤ 0.85 OR mean attainment below gamma by ≥ 5 pp (cascade/overshed).
- P3b: |gamma mean goodput − maxej10 mean goodput| ≤ 5 pp (consistency at this N).
- P3c: gamma mean goodput ≥ minhealth50 mean goodput − 5 pp.
