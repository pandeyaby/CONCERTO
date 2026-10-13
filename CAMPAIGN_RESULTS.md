# CONCERTO testbed campaign results (PREREG v3)

Pre-registration: `PREREG.md` v3 (committed before any v3 trial).  
Branch: `cursor/genesisgttestbed-campaign-ebe8`.  
Machine: single-node k3s v1.31.4 + Envoy v1.31.4 + prometheus-adapter.

**Primary verdicts use the original gap-validity rule.** Relaxed-rule numbers are secondary and disclosed because the acceptance criterion was changed mid-campaign.

---

## Gap-validity rules (disclose)

| Rule | Criterion (HPA arms) | Role |
|---|---|---|
| **Original (primary)** | `phase2_duration_s ≥ 470` **and** `max_sample_gap_s ≤ 10` | Pre-campaign / RQ1 bar. **Authoritative for PASS/FAIL.** |
| **Relaxed (secondary)** | `phase2 ≥ 470` **and** `gap ≤ 600` **and** `rep_n ≥ 60` **and** `final_replicas` set | Added mid-campaign after kubectl API stalls left multi-minute gaps in `replicas.csv` while vegeta windows stayed complete. Tagged `sampling: degraded` when used. |

P3 arms (180 s, no HPA): `phase2 ≥ 170` and `n ≥ 1000` under both rules.

Vegeta binaries stay gitignored; committed artifacts are `replicas.csv`, optional `clusters.txt`, and `results_campaign.json` / `dual_verdicts.json`.

Reproduce dual tables: `python3 testbed/dual_verdicts.py`.

---

## Trials affected by the mid-campaign relaxation

Accepted under **relaxed only** (fail original `gap ≤ 10`):

| Trial | gap (s) | attain | final repl. | original | relaxed |
|---|---:|---:|---:|---|---|
| `tt_indep_1b` | 376 | 0.4999 | 3 | FAIL | PASS (degraded) |
| `tt_safe_2` | 424 | 1.000 | 5 | FAIL | PASS (degraded) |

All other committed campaign trials pass **both** rules (`gap = 6`).

Attempts invalid under **both** rules (recorded, not used in either verdict column):

| Attempt | gap (s) | attain | final repl. | notes |
|---|---:|---:|---:|---|
| `p1_budget_2` / `p1_budget_2b` | 1112 / 920 | 0.25 | 2 | later replaced by valid `p1_budget_2c` |
| `tt_indep_2` (first) | 917 | 0.5 | 3 | replaced by `tt_indep_2b` |
| `tt_safe_3` | 907 | 1.0 | 5 | replaced by `tt_safe_3b` (gap 6) |
| `invalid_ac_reverse_2_freeze` | 4911 | ~1.0 | 5 | box freeze; replaced by fresh `ac_reverse_2` |

First `tt_indep_1` attempt (gap 308) would be relaxed-only; superseded by clean `tt_indep_1` (gap 6). Kept under `runs/invalid/`.

---

## Verdict summary

| Hypothesis | Original (primary) | Relaxed (secondary) |
|---|---|---|
| **AC1** trap ≤2 repl, attain ≤0.45 | **PASS** (3/3) | PASS (3/3) |
| **AC2** reverse ≥5 repl, attain ≥0.85 | **PASS** (3/3) | PASS (3/3) |
| **AC3** mean gap ≥0.3 | **PASS** (1.000−0.286) | PASS |
| **TT1** indep attain ≤0.55 | **PASS** (3 orig indep) | PASS (4 incl. 1b) |
| **TT2** safe−indep ≥0.25 | **PASS** | PASS |
| **TT3** safe ≥4 replicas | **PASS** (2 orig safe; incomplete n) | PASS (3 safe incl. degraded `tt_safe_2`) |
| **P1a** P1 attain ≥ indep−5 pp | **FAIL** (0.25 vs 0.50) | FAIL |
| **P1b** P1 replicas ≥ indep | **FAIL** (2 vs 3) | FAIL |
| **P1c** P1 within 15 pp of safe | **FAIL** (0.25 vs ~0.995) | FAIL |
| **P3a** none worse / cascade | **FAIL** (all policies ≈0.997) | FAIL |
| **P3b** \|gamma−maxej10\| ≤5 pp | **PASS** | PASS |
| **P3c** gamma ≥ minhealth−5 pp | **PASS** | PASS |

Incomplete under **original** only: TT safe arm has 2 of 3 (`tt_safe_1`, `tt_safe_3b`); `tt_safe_2` counts only under relaxed. Hypotheses TT1–TT3 still PASS on the original-valid subset.

---

## Per-arm numbers (original-valid trials unless noted)

### E-AC (adaptive concurrency trap)

| Trial | attain | frac_503 | final / mean repl. | gap |
|---|---:|---:|---:|---:|
| ac_trap_1 | 0.2855 | 0.7145 | 2 / 2.00 | 6 |
| ac_trap_2 | 0.2853 | 0.7147 | 2 / 2.00 | 6 |
| ac_trap_3 | 0.2858 | 0.7142 | 2 / 2.00 | 6 |
| ac_reverse_1 | 1.0000 | 0.0000 | 5 / 5.00 | 6 |
| ac_reverse_2 | 1.0000 | 0.0000 | 5 / 5.00 | 6 |
| ac_reverse_3 | 1.0000 | 0.0000 | 5 / 5.00 | 6 |

Same observation-coupling trap as RQ1, on the AC 503 path with concurrency pinned (`min_concurrency = max_concurrency_limit`).

### E-two-tier

| Trial | rule | attain | frac_429 | final / mean repl. | gap |
|---|---|---:|---:|---:|---:|
| tt_safe_1 | both | 0.9916 | 0.0000 | 5 / 5.00 | 6 |
| tt_safe_2 | **relaxed only** | 1.0000 | 0.0000 | 5 / 5.00 | 424 |
| tt_safe_3b | both | 0.9986 | 0.0000 | 5 / 5.00 | 6 |
| tt_indep_1 | both | 0.5000 | 0.5000 | 3 / 3.00 | 6 |
| tt_indep_1b | **relaxed only** | 0.4999 | 0.5000 | 3 / 3.00 | 376 |
| tt_indep_2b | both | 0.5000 | 0.5000 | 3 / 3.00 | 6 |
| tt_indep_3 | both | 0.5000 | 0.5000 | 3 / 3.00 | 6 |

Edge `R=80` caps admitted load at half of the 160 req/s offer → attain 0.50 under independent two-tier shedding.

### E-P1 (shared budget stand-in: edge 50 + side 25)

| Trial | attain | frac_429 | final / mean repl. | gap |
|---|---:|---:|---:|---:|
| p1_budget_1 | 0.2500 | 0.7500 | 2 / 2.00 | 6 |
| p1_budget_2c | 0.2500 | 0.7500 | 2 / 2.00 | 6 |
| p1_budget_3 | 0.2500 | 0.7500 | 2 / 2.00 | 6 |

Budgeting made attainment **worse** than TT-INDEP (edge 50 admits less than edge 80). This stand-in does not implement proportional redistribution of a shared severity budget; it only lowers configured rates. P1a–P1c all **FAIL**.

### E-P3 (outlier caps, 10 endpoints, 200 req/s × 180 s)

| Policy | mean attain (3 trials) | mean frac_503 |
|---|---:|---:|
| none | 0.9968 | ~0.0032 |
| maxej10 | 0.9968 | ~0.0031 |
| minhealth50 | 0.9968 | ~0.0031 |
| gamma | 0.9968 | ~0.0032 |

One always-503 fault pod among 10 endpoints produces ~0.3% 503s and does **not** trigger a measurable cascade under these Envoy settings; policies are indistinguishable → P3a **FAIL**, P3b/P3c **PASS** as consistency checks.

---

## Operational notes

- Commits pushed after every valid trial via `testbed/commit_trial.sh`.
- Mid-run box freeze invalidated one AC reverse (4911 s gap); rerun succeeded.
- Replica sampler later gained `timeout 8` around kubectl; push failures no longer mark trials invalid.
- Brief reconstruction: original agent prompt was lost; arms taken from run title `(P3, P1, AC trap, two-tier)` + PREREG v3.

---

## Artifacts

- `testbed/results_campaign.json` — accepted trials (includes degraded where tagged)
- `testbed/dual_verdicts.json` — full per-trial flags + both verdict objects
- `testbed/runs/<label>/replicas.csv` (+ `clusters.txt` for P3)
- `PREREG.md` v3
