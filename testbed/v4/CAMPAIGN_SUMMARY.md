# v4 campaign summary (in progress)

## Contaminated run excluded

| Label | Role | attain | final_replicas | Notes |
|-------|------|--------|----------------|-------|
| `excluded_p1_indep_2` | EXCLUDED | 0.6935 | 3 | Orphan `p1_ctl` from `p1_p1ctl_2b` capped shared edge admin for the whole run. Files retained; not used in verdicts. |
| `p1_indep_2` | clean rerun | 0.2632 | 2 | Verified INDEP caps (edge=8, sidecar=2, no runtime overrides). Valid. |
| `p1_indep_1` | reference | 0.2631 | 2 | Uncontaminated trap baseline. |

## P1 verdict impact (provisional)

Official V1–V4 require 3 valid trials per arm; the campaign was stopped mid-stream, so `analyze.py` emits no V/G verdicts yet.

Using INDEP means from the two available valid indep trials:

- **If contaminated indep_2 had been kept:** INDEP mean ≈ (0.2631+0.6935)/2 = **0.4783** → V1 bar = INDEP+0.25 ≈ **0.728**. With current sole valid P1CTL (`p1_p1ctl_1` attain 0.6981), provisional V1 would be **FAIL**.
- **With clean indep_2:** INDEP mean ≈ (0.2631+0.2632)/2 = **0.26315** → V1 bar ≈ **0.513**. Same P1CTL attain 0.6981 → provisional V1 would be **PASS**.

So replacing the contaminated result with the clean rerun **changes the provisional V1 direction** (FAIL → PASS) on currently available trials. Full V1–V4 still await completing N=3 per arm (and a valid `p1_p1ctl_2` / `p1_p1ctl_3`).

## Harness notes

See `NOTES.md` §6–§7. PR #2 remains draft; not merged.
