# v6 campaign summary (complete)

PREREG v6 P1 generalization (setting B: ramp 40→200 req/s). Harness: `COMMIT=1 ./run_all.sh` on branch `v6-campaign` from `main@270e968`. No amendments (v6-A1…) — campaign executed as pre-registered.

## n_valid

| Arm | n_valid | required |
|-----|---------|----------|
| p1_indep | 5 | 5 |
| p1_p1ctl | 5 | 5 |
| p1_safe | 5 | 5 |

Zero invalid trials. Zero reruns (`*b` / `*c`). No harness contamination.

## Per-arm means (final 240 s attainment; valid trials only)

| Arm | mean attain | mean final_replicas | mean p99_ms_first120 |
|-----|-------------|---------------------|----------------------|
| p1_indep | 0.2163 | 2.0 | 273.7 |
| p1_p1ctl | 0.9964 | 8.0 | 139.28 |
| p1_safe | 0.9995 | 8.0 | 88.44 |

Per-trial attain / final_replicas:

- INDEP: 0.2157/2, 0.215/2, 0.2136/2, 0.2183/2, 0.219/2
- P1CTL: 0.9977/8, 0.9962/8, 0.997/8, 0.9959/8, 0.9954/8
- SAFE: 0.9994/8, 0.9994/8, 0.9996/8, 0.9997/8, 0.9994/8

## Official verdicts

| Claim | Verdict | Notes |
|-------|---------|-------|
| W0 | **PASS** | 5/5 SAFE trials end with ≥ 7 replicas (need ≥ 4 of 5); all ended at 8 |
| V1 | **PASS** | P1CTL mean attain 0.9964 ≥ INDEP 0.2163 + 0.25 (= 0.4663) |
| V2 | **PASS** | every valid P1CTL trial ends with ≥ 6 replicas (all 8) |
| V3 | **PASS** | P1CTL mean attain 0.9964 ≥ SAFE 0.9995 − 0.05 (= 0.9495) |
| V4 | **FAIL** | P1CTL mean p99 first-120s 139.28 ≰ 0.8 × SAFE 88.44 (= 70.752); reported separately |

**Generalization verdict** (PREREG v6): P1 “generalizes to setting B” iff W0 and V1–V3 all PASS: **yes**. V4 (early-window latency) fails and does not change the verdict.

## Final replicas vs prediction

PREREG predicted range **7–8**, point **8**. Observed: every valid SAFE and P1CTL trial ended at **8**; every INDEP trial stayed at **2** (trap). Matches the point prediction.

## Invalid trials

None. Every scheduled label `p1_{p1ctl,indep,safe}_{1..5}` completed valid on the first attempt (dur=481–484 s ≥ 470, max replica-sample gap=6 s ≤ 10 s, wall-clock sampler).

## Plant note (observational, not an amendment)

Same plant/HPA/rule as v5; only the load shape changed. SAFE and P1CTL scaled through the ramp to the maxReplicas cap (8); INDEP remained trapped at 2 (sidecar cap 2). No VM suspend; wall-clock gap rule held throughout.
