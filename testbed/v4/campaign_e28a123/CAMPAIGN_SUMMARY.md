# v4 campaign summary (complete)

## Official verdicts

| Claim | Verdict | Notes |
|-------|---------|-------|
| V1 | **INCONCLUSIVE** | Only **2** valid P1CTL trials (`p1_p1ctl_1`, `p1_p1ctl_3`). `p1_p1ctl_2` + one-shot rerun `p1_p1ctl_2b` both invalid (gap ≫ 10 s from VM suspend). PREREG requires 3/arm; `analyze.py` does not emit V1–V4. |
| V2 | **INCONCLUSIVE** | same |
| V3 | **INCONCLUSIVE** | same |
| V4 | **INCONCLUSIVE** | same |
| G0 | **PASS** | mean max concurrent ejections UNCAPPED = 7 ≥ 4 |
| G1 | **FAIL** | GAMMA mean goodput 0.9145 ≱ UNCAPPED 0.8987 + 0.05 |
| G2 | **PASS** | GAMMA 0.9145 ≥ CAP10 0.9191 − 0.02 |
| G3 | **PASS** | faulty ejected at end in 3/3 GAMMA trials |

P1 “supported on the testbed” (V1–V3 all pass): **not established** (V1–V3 INCONCLUSIVE).

## Contaminated / invalid / aborted (retained, not in verdict arms)

| Label | Reason |
|-------|--------|
| `excluded_p1_indep_2` | Contaminated by orphan `p1_ctl` from `p1_p1ctl_2b` (attain 0.6935 / 3 replicas). Clean rerun is `p1_indep_2`. |
| `invalid_p1_p1ctl_2` | gap 1823 s (VM suspend) |
| `p1_p1ctl_2b` | one-shot rerun; gap 2405 s (still invalid) |
| `aborted_p1_p1ctl_3` | stopped mid-load for clean indep_2 restart; superseded by fresh `p1_p1ctl_3` |

## Means (valid, non-excluded)

- INDEP attain mean 0.2646 (n=3); P1CTL 0.6897 (n=2); SAFE 0.8927 (n=3)
- UNCAPPED goodput 0.8987; CAP10 0.9191; GAMMA 0.9145 (all n=3)
