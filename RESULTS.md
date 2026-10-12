# Results v0.1.0 (simulator only; see the "does not claim" list in results/ledger.json)
Pre-registration: PREREG.md, committed before these runs. Reproduce with `python3 -m concerto_sim` (deterministic, about 30 s).

| Hypothesis | Verdict | Numbers |
|---|---|---|
| H1a independent unstable for m≥2 | PASS | Σρ = 1.2–3.0, growing for m = 2..5 |
| H1b P1 stable, settling time flat | PASS | 5.77 s for every m = 1..5 |
| H1c P1 cost at m=1 ≤1.5× | PASS | 5.77 s vs. 7.61 s (P1 is faster because ρ 0.6→0.5 cuts overshoot) |
| H3a Γ prediction agreement ≥80% | PASS (weak) | 180/180 agree. Outcomes are bimodal: no cascade at u ≤ 0.85, total collapse (49 extra ejections) at u ≥ 0.9 |
| H3b gate ≥ max_ejection −1pp | PASS | Equal (1.0) at u ≤ 0.85. +2.6 pp [2.4, 2.8] at 0.9, +6.2 pp [5.8, 6.6] at 0.95 |
| H3c gate beats both somewhere | PASS | vs. minHealth50: +2.9 pp at 0.9, +3.1 pp at 0.95 |
| H-RQ3 B4 ≥ best baseline −1pp, cost ≤1.15× | **FAIL** | Best baseline is B2. Attainment B4 0.916 vs. B2 0.993 (−7.7 pp [−7.9, −7.5]). Cost 0.69× B2 |
| H-RQ4 P1 → osc | PASS | Without P1, osc +0.022 [0.021, 0.023] |
| H-RQ4 P2 → attain | PASS | Without P2, attainment −56.8 pp (0.348 vs. 0.916) |
| H-RQ4 P4 → replica changes | PASS, with a cost | Without P4: +9.05 changes, but attainment is HIGHER (0.956 vs. 0.916) |
| H-RQ2 B2 fixes osc but not attainment | **FAIL** | B2 cuts osc (−0.19), but B2 attainment exceeds B4 by +7.7 pp. Retuning (target 0.55, gains ×0.4) escapes the trap |

Notes. B4 still sheds because its limiters trip at 60% while P2 provisions to a 70% target. CONCERTO
does not fix threshold ordering. B2 buys its attainment with 28.0 replicas vs. B4's 19.2.
The P3 result rests on a goodput model in which not ejecting an overloaded host is nearly free.
