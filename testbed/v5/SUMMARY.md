<!-- Provenance: copied from remote branch v5-campaign (draft PR #3), testbed/v5/SUMMARY.md and testbed/v5/results_v5.json, fetched read-only 2026-10-13. Per-trial runs/ remain on v5-campaign. -->
# v5 campaign summary (complete)

PREREG v5 P1 powered rerun. Harness: `COMMIT=1 ./run_all.sh` on branch `v5-campaign` from `main@9dba530`. No amendments (v5-A1…) — campaign executed as pre-registered.

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
| p1_indep | 0.2689 | 2.0 | 316.7 |
| p1_p1ctl | 0.9943 | 6.0 | 151.74 |
| p1_safe | 0.9998 | 6.0 | 141.82 |

Per-trial attain / final_replicas:

- INDEP: 0.268/2, 0.2698/2, 0.2673/2, 0.2716/2, 0.2679/2
- P1CTL: 0.9932/6, 0.9939/6, 0.9952/6, 0.9949/6, 0.9943/6
- SAFE: 0.9998/6, 0.9998/6, 0.9997/6, 0.9998/6, 0.9999/6

## Official verdicts

| Claim | Verdict | Notes |
|-------|---------|-------|
| W0 | **PASS** | 5/5 SAFE trials end with ≥ 6 replicas (need ≥ 4 of 5) |
| V1 | **PASS** | P1CTL mean attain 0.9943 ≥ INDEP 0.2689 + 0.25 (= 0.5189) |
| V2 | **PASS** | every valid P1CTL trial ends with ≥ 5 replicas (all 6) |
| V3 | **PASS** | P1CTL mean attain 0.9943 ≥ SAFE 0.9998 − 0.05 (= 0.9498) |
| V4 | **FAIL** | P1CTL mean p99 first-120s 151.74 ≰ 0.8 × SAFE 141.82 (= 113.456); reported separately |

P1 “supported on the testbed” (W0 and V1–V3 all pass): **yes**. V4 (early-window latency) fails and is reported separately per PREREG v5.

## Invalid trials

None. Every scheduled label `p1_{p1ctl,indep,safe}_{1..5}` completed valid on the first attempt (dur=480 s, max replica-sample gap=6 s ≤ 10 s, wall-clock sampler).

## Plant note (observational, not an amendment)

HPA target 25 with measured ~36.8 req/s/pod calibration worked as designed: SAFE and P1CTL consistently reached 6 replicas; INDEP stayed trapped at 2 (sidecar cap 2). No VM suspend; wall-clock gap rule held throughout.
