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

# Pre-registration v3a (main 64adf88, 2026-10-12; committed before any run). NOT EXECUTED: superseded by v3b below before any v3 trial; these designs remain untested
Same box, k3s, Envoy v1.31.4 and analysis conventions as v2. A trial is valid only if its load phase completes and
its max sample gap is ≤ 10 s. Invalid trials are rerun and reported.

## TB-P3: outlier-ejection cascades on a pool
Setup: 10 app pods. Each pod's capacity is drawn from {37.5, 50, 62.5} req/s by a hash of the pod name.
A bounded queue (8 in-flight) answers 503 when full. One pod is faulty and answers 503 to every request.
Edge Envoy outlier detection: consecutive_5xx = 5, interval 2 s, base_ejection_time 30 s.
Open-loop load is 0.85 × total capacity for 300 s. Metrics cover the last 180 s.
Arms:
- UNCAPPED: max_ejection_percent = 100, panic threshold 50% (the Envoy default).
- CAP10: max_ejection_percent = 10 (the Envoy default).
- GAMMA: max_ejection_percent is driven at runtime by an external controller that admits one more ejection
  only if the projected Γ is < 1.
Trials: 3 per arm (5 if time allows).
- P3a: mean goodput (2xx fraction) of GAMMA ≥ CAP10 − 0.02.
- P3b: GAMMA goodput > UNCAPPED goodput by ≥ 0.05 (mean).
- P3c: GAMMA ejects the faulty pod in ≥ 2/3 of its trials (not starving the needed ejection).

## TB-P1: shared authority on one variable
Arms:
- INDEP: Envoy adaptive concurrency + local rate limit + retries (retry_on 5xx, 2 retries), all active.
- BUDGET: the same mechanisms, with an external allocator that every 5 s rescales the concurrency/rate limits
  so the summed limits track one shared target.
Workload: step to 1.2× capacity.
- P1a: BUDGET oscillation, sd of 1-s admitted rate over the last 180 s, ≤ 0.8 × INDEP.
- P1b: BUDGET attainment ≥ INDEP − 0.02.

## TB-RQ1-AC: trap with adaptive concurrency as the shedder
Same as v2, with the per-pod token bucket replaced by adaptive_concurrency and HPA target 35 req/s. The trip
point is set by latency, so it is reported as measured.
- AC1: if the measured admitted rate per pod at saturation is below 35, TRAP behaviour reproduces
  (≤ 2 replicas, attainment ≤ 0.6). Otherwise we report that adaptive concurrency did not create the ordering.

## Second app and trial counts
A two-tier variant (frontend → backend) for RQ1 with the token bucket, ≥ 3 trials per arm, same T1–T3 thresholds.
Where time allows, existing arms are extended to 5 trials.
Each item is reported as completed, partial, or not run.
# Pre-registration v3b: testbed campaign (P3, P1, AC trap, two-tier). Written by the campaign agent (122d3c7, 2026-10-13 00:21 UTC) before any v3 trial; it replaced v3a on that branch. Campaign verdicts refer to v3b
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

# Pre-registration v4: the real remedies (committed before any v4 trial; smoke runs are labelled smoke_* and excluded)
Code: `testbed/v4/` (p1.yaml.tpl, p1_ctl.py, p3_pool.yaml.tpl, gamma_ctl.py, trial.sh, analyze.py, run_all.sh).
Same stack as v2/v3b. Validity (primary, unchanged): load phase complete (P1 ≥ 470 s, P3 ≥ 290 s) and sample gap ≤ 10 s.
Invalid trials are rerun once as `<label>b` and every invalid trial is reported. No relaxed rule will be used for verdicts.
Trials: 3 per arm (N=3), interleaved.

## V: threshold-aware shared budget (P1 as designed)
Plant: 50 req/s pods; a per-pod sidecar Envoy concurrency shedder (circuit-breaker overflow → 503); an edge Envoy
concurrency shedder; HPA on per-pod 2xx, target 35 req/s, 2–8 replicas. Load: 50 req/s for 60 s, then 160 req/s for 480 s.
- INDEP: sidecar cap 2 (≈25 req/s, below target) and edge cap 8. This is the trap configuration.
- P1CTL: starts from the INDEP configuration. The external controller p1_ctl.py adjusts both caps every 5 s via Envoy
  runtime. (i) Threshold constraint: no sidecar trips below 1.15 × target. (ii) Severity-scaled budget: edge cap =
  n_ready × 50 req/s × 0.08 s × (1 + 0.10 + 0.20·(1 − s)).
- SAFE: sidecar cap 6, edge cap 1000 (shedding effectively off).
Hypotheses (metrics on the final 240 s unless noted):
- V1: P1CTL mean attainment ≥ INDEP + 0.25.
- V2: every P1CTL trial ends with ≥ 5 replicas.
- V3: P1CTL mean attainment ≥ SAFE − 0.05.
- V4 (protection retained): P1CTL p99 latency of 2xx responses in the first 120 s of the 160 req/s phase ≤ 0.8 × SAFE.
P1 is "supported on the testbed" only if V1–V3 all pass. V4 is reported separately.

## G: Γ-gated ejection on a pool that can cascade
Pool: 10 pods with capacity 37.5, 50 or 62.5 req/s (by a hash of the pod name) and an 8-in-flight queue (503 when full).
One pod is made faulty (503 always). Edge outlier detection: consecutive_5xx 5, interval 2 s, base ejection 30 s, panic
threshold 50%. Load 0.90 × total capacity, open loop, 300 s; metrics over the final 180 s.
- UNCAPPED: max_ejection_percent 100.
- CAP10: max_ejection_percent 10.
- GAMMA: max_ejection_percent driven at runtime by gamma_ctl.py (dynamic Γ). One more ejection is admitted only if a
  failing host has projected Γ < 1, or is dead (success < 10%). The dead-host exception is part of the design.
- G0 (informativeness gate): mean max concurrent ejections under UNCAPPED ≥ 4. If G0 fails, G1–G3 are INCONCLUSIVE
  (no cascade occurred) and are not reported as PASS or FAIL.
- G1: GAMMA mean goodput ≥ UNCAPPED + 0.05.
- G2: GAMMA mean goodput ≥ CAP10 − 0.02.
- G3: GAMMA has the faulty pod ejected at the end of ≥ 2 of 3 trials.

### v4 amendment A1 (smoke, before any v4 trial)
The P1 smoke (not a trial) showed that `max_pending_requests: 0` rejects every request: Envoy routes every HTTP/1
request through the pending queue. Both shedders now use `max_pending_requests: 1`. Hypotheses, arms and thresholds
are unchanged. Smoke results, for disclosure only: 2 pods at 100 req/s served 41% under the static trap caps and 69%
with p1_ctl.py running. The controller wrote edge cap 11 and sidecar cap 4 through the runtime API as designed.

# Pre-registration v5: properly powered P1 rerun (committed before any v5 trial; v1–v4 above are unchanged)
Scope: P1 only (threshold-aware shared authority budget). Code: `testbed/v5/` (p1.yaml.tpl, p1_ctl.py, trial.sh,
run_all.sh, analyze.py). Results go under `testbed/v5/runs/` and `testbed/v5/results_v5.json`.

## Why v5: real per-pod throughput (derived from v4 data, before any v5 trial)
v4 P1 was INCONCLUSIVE (2 valid P1CTL trials). In every v4 P1 trial that ended saturated at 3 replicas, final-240 s
goodput was 0.6813–0.7013 of 160 req/s (P1CTL 0.6981, 0.6813, invalid 0.6967/0.7013, aborted 0.6996; SAFE trial
p1_safe_2 0.6783; contaminated INDEP 0.6935). Goodput × 160 / 3 gives a **measured per-pod throughput of 36.2–37.4 req/s,
mean ≈ 36.8 req/s**, not the nominal 50 (4 workers × 80 ms; the gap is per-request Python/Envoy/`keepalive=false`
connection overhead). The v4 HPA target was 35 req/s/pod: at 3 saturated pods the HPA ratio is 36.8/35 ≈ 1.05, which is
inside the HPA's default 10 % tolerance, so the HPA never scaled. That is why P1CTL and p1_safe_2 got stuck at 3. The v4
design was underpowered/miscalibrated. This is a plant calibration fault, not evidence about P1.

## Parameters (changes from v4 V in bold; everything else is identical to v4 V + amendment A1)
- Plant: same v4 P1 plant (pods nominally 50 req/s, measured ≈ 36.8; sidecar and edge Envoy concurrency shedders with
  `max_pending_requests: 1`; HPA on per-pod 2xx `envoy_ok_rps`, 2–8 replicas). Namespace `v5p1`.
- **HPA target 25 req/s/pod** (= 68 % of the measured 36.8). A saturated pod then gives ratio ≥ 1.47 ≫ 1.10 tolerance.
  Needed replicas at 160 req/s: ceil(160/25) = 7 (≤ max 8).
- Load: unchanged. 50 req/s for 60 s, then 160 req/s for 480 s, open loop, `keepalive=false`.
- INDEP: sidecar cap 2 (trips at ≈ 2/0.109 ≈ 18 req/s/pod, below the 25 target, so it is still the trap), edge cap 8.
- P1CTL: starts from INDEP. p1_ctl.py with **TARGET = 25, POD_CAP = 36.8 (measured), SVC = W/POD_CAP = 0.109 s**, M = 0.15,
  W = 4. Threshold-aware rule (unchanged form): sidecar cap = max(W, ceil((1+M)·TARGET·SVC)) = max(4, ceil(3.13)) = **4**,
  so no sidecar trips below 1.15 × target (4/0.109 ≈ 36.7 req/s ≥ 28.75). Edge cap = ceil(n_ready·POD_CAP·SVC·(1+0.10+0.20·(1−s))).
- SAFE: sidecar cap 6, edge cap 1000 (unchanged).

## Validity and harness
- Valid iff load phase ≥ 470 s and max replica-sample gap ≤ 10 s, with the gap measured on **wall-clock** timestamps
  (`date +%s`). The v4 mid-campaign switch to monotonic time is not used. A VM suspend makes a trial invalid, which is right
  for a control-loop experiment, because the HPA/controller clocks also stall.
- **Cleanup between trials:** trial.sh kills any `p1_ctl.py`, `vegeta` and sampler processes before and after each trial and
  aborts (exit 3) if any survive. The namespace is deleted and recreated per trial (as in v4). This prevents the orphan
  controller contamination seen in v4 (`excluded_p1_indep_2`).
- **N = 5 trials per arm**, interleaved p1ctl, indep, safe × 5.
- **Rerun policy (fixed now):** an invalid trial is renamed `invalid_<label>` and rerun as `<label>b`, then `<label>c` at most.
  Every invalid trial is reported. No other exclusions. Any trial with harness contamination is reported, not silently dropped.
  If any arm has < 5 valid trials, all of V1–V4 are INCONCLUSIVE.
- setup.sh fix (v4 NOTES item 4, never landed on main): capture `TESTBED_DIR` before `cd /tmp`, and the adapter install is
  no longer `|| true` so a failure is visible. Not a design change.

## Hypotheses (final 240 s unless noted; same thresholds as v4 V)
- W0 (informativeness gate, new): ≥ 4 of 5 SAFE trials end with ≥ 6 replicas. If W0 fails, the plant still doesn't scale
  and V1–V4 are INCONCLUSIVE.
- V1: P1CTL mean attainment ≥ INDEP mean + 0.25.
- V2: every valid P1CTL trial ends with ≥ 5 replicas.
- V3: P1CTL mean attainment ≥ SAFE mean − 0.05.
- V4 (reported separately): P1CTL mean p99 2xx latency in the first 120 s of the 160 req/s phase ≤ 0.8 × SAFE.
P1 is "supported on the testbed" only if W0 and V1–V3 all pass. Any deviation during the campaign is recorded as a
numbered, disclosed amendment (v5-A1, …) appended below this section; v1–v5 text is never edited.

# Pre-registration v6: generalization of P1 to a second load shape (committed before any v6 trial; v1–v5 above are unchanged)
Scope: P1 only. Question: does the v5 result (W0, V1–V3 PASS) hold when the disturbance is a **ramp to a higher peak**
instead of one step? Code: `testbed/v6/` (copy of `testbed/v5/` with minimal changes: namespace `v6p1`, load shape in
trial.sh, ramp files and replica thresholds in analyze.py). Results: `testbed/v6/runs/`, `testbed/v6/results_v6.json`.

## Setting B and why
- **Load (the only design change):** 40 req/s for 60 s (warm-up, not scored); then a staircase ramp 50, 60, …, 200 req/s
  (16 steps × 15 s = 240 s); then 200 req/s held for 240 s. Open loop, `keepalive=false`, timeout 10 s. Vegeta 12 has
  no linear-ramp CLI pacer, so the ramp is 16 back-to-back constant-rate attacks. Load phase = ramp + hold = 480 s,
  which matches v5, so the validity rule and the 240 s scoring window carry over unchanged.
- **Why a ramp to 200 and not a new service time.** (1) A ramp is a qualitatively different disturbance: the controller
  must track a moving demand while the HPA scales in several stages, not react once to a step. (2) The higher peak
  needs the maximum fleet (8 replicas, see below), so it tests whether the budget keeps scaling all the way up rather than
  only to the mid-range. (3) Changing the pod service time would need a new POD_CAP calibration run before the
  rule can be applied. That is a second unregistered measurement, and it would change the plant and the load together.
  Keeping the plant fixed isolates the load shape, and it lets the rule's inputs (TARGET 25, POD_CAP 36.8, SVC 0.109,
  M 0.15, W 4) be reused exactly. (4) Feasibility: 8 × 36.8 ≈ 294 req/s of capacity ≥ 200. A trial is ≈ 9 min of load
  plus ≈ 2–3 min of namespace setup, so 15 trials take ≈ 3 h.
- Repeated bursts were considered and rejected: the HPA's 5-min scale-down stabilization keeps replicas high
  between bursts, so later bursts would not exercise the trap. That makes the design less informative per hour.

## Parameters (identical to v5 except load and namespace)
- Plant, HPA (target 25 req/s/pod `envoy_ok_rps`, 2–8 replicas, default 10 % tolerance), shedders: as v5.
- INDEP: sidecar cap 2, edge cap 8. SAFE: sidecar cap 6, edge cap 1000.
- P1CTL: p1_ctl.py **byte-identical in logic to v5** (TARGET 25, POD_CAP 36.8, SVC 0.109, M 0.15, W 4). By the same
  threshold-aware rule: sidecar cap = max(4, ceil(1.15·25·0.109)) = 4; edge cap = ceil(n·36.8·0.109·(1.10+0.20(1−s))),
  e.g. 42 at n = 8, s = 0. No parameter is tuned to setting B.

## Replica prediction (and the v5 6-vs-7 explained)
The HPA sets desired = ceil(n · m/T) and does nothing while |m/T − 1| ≤ 0.10 (m = mean per-pod 2xx rate, T = 25).
With load L fully served by n pods, m = L/n. Every n with L/(1.10·T) ≤ n ≤ L/(0.90·T) is a resting point. At
L = 160 that is 5.82 ≤ n ≤ 7.11, so n ∈ {6, 7}. v5 predicted ceil(160/25) = 7, which ignored the tolerance band. Once
at 6 (160/6 = 26.7, ratio 1.067), the HPA stops, and scale-down is never triggered. The pre-scale-up metric lag
(new pods enter the average with near-zero rate) makes the lower edge of the band the typical landing point. So
6 was a correct outcome of the HPA and not a plant fault. The v5 verdicts are unaffected, since W0 used ≥ 6 and V2 used ≥ 5.
For v6 at L = 200: band 200/27.5 = 7.27 ≤ n ≤ 200/22.5 = 8.9, capped at maxReplicas 8, so **n = 8 predicted** for SAFE
and P1CTL. 7 is possible only if a trial ends while still scaling (7 pods: 28.6/25 = 1.14 > 1.10, so the HPA scales out).
**Predicted range 7–8, point 8.** INDEP: predicted to stay at 2 (each sidecar trips at ≈ 18 req/s/pod < 25, and the
edge cap 8 admits ≈ 73 req/s). Predicted INDEP attainment ≈ 0.15–0.25, P1CTL ≥ 0.97, SAFE ≥ 0.99.

## Validity, harness, rerun policy (identical to v5)
- Valid iff load phase (first ramp request to last hold request) ≥ 470 s and max wall-clock replica-sample gap ≤ 10 s.
- Cleanup of p1_ctl.py, vegeta and sampler processes before and after every trial (abort with exit 3 if any survive).
  The namespace is deleted and recreated per trial.
- N = 5 per arm, interleaved p1ctl, indep, safe × 5. An invalid trial is renamed `invalid_<label>` and rerun as
  `<label>b`, then `<label>c`. Every invalid trial is reported. If any arm has < 5 valid trials, all verdicts are INCONCLUSIVE.

## Hypotheses (attainment on the final 240 s = the 200 req/s hold; fixed before any data)
- W0 (informativeness gate): ≥ 4 of 5 SAFE trials end with ≥ 7 replicas. If W0 fails, V1–V4 are INCONCLUSIVE.
- V1: P1CTL mean attainment ≥ INDEP mean + 0.25.
- V2: every valid P1CTL trial ends with ≥ 6 replicas.
- V3: P1CTL mean attainment ≥ SAFE mean − 0.05.
- V4 (secondary, reported separately): P1CTL mean p99 2xx latency in the first 120 s of the load phase ≤ 0.8 × SAFE.
- Replica thresholds are set relative to the predicted 8 the same way v5's were relative to its prediction (W0 one
  below the point, V2 two below). Thresholds for V1, V3 and V4 are unchanged.
**Generalization verdict:** P1 "generalizes to setting B" iff W0, V1, V2 and V3 all PASS. If W0 passes and any of
V1–V3 fails, P1 **does not generalize** to setting B and the paper must scope the v5 claim to the step load. If W0 fails,
the result is INCONCLUSIVE. V4 never changes the verdict. Deviations are recorded as appended amendments v6-A1, …
below this section. No PREREG text (v1–v6) is edited.
