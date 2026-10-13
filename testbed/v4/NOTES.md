# v4 harness notes (disclosures only; PREREG thresholds/arms/validity unchanged)

## 2026-10-13 — harness fixes before campaign start

1. **`run_all.sh` push after trial commit.** With `COMMIT=1`, the harness already committed each completed trial (including a one-shot `<label>b` rerun). Added `git push -u origin HEAD` after that commit so the `v4-campaign` remote branch advances after every trial, as required for this campaign run.

2. **`analyze.py` `invalid_*` trial classification.** Invalid trials are renamed to `invalid_<label>`. The previous analyzer treated any non-`p1_*` directory name as P3, so `invalid_p1_*` rows errored instead of being scored under the P1 validity/metrics path. Fixed by stripping the `invalid_` prefix before choosing `a_p1` vs `a_p3`. Verdicts still use only valid, non-`invalid_*` trials. Thresholds, arms, and the gap ≤ 10 s / duration rules are unchanged.

3. **`analyze.py` G0 → G1–G3 INCONCLUSIVE.** When `G0_informative` is false, emit `G1`/`G2`/`G3` as the string `INCONCLUSIVE` rather than omitting them or mapping a boolean to FAIL, matching PREREG v4 (“If G0 fails, G1–G3 are INCONCLUSIVE … and are not reported as PASS or FAIL”).
