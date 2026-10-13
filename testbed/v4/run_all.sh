#!/bin/bash
# Full v4 campaign, interleaved arms; reruns an invalid trial once as <label>b. Commit after each trial if COMMIT=1.
cd "$(dirname "$0")"; N=${N:-3}
one() { ./trial.sh "$@"; v=$(python3 -c "import analyze as a,sys;print((a.a_p1 if '$1'=='p1' else a.a_p3)('runs/$3')['valid'])" 2>/dev/null); \
  [ "$v" = True ] || { mv runs/$3 runs/invalid_$3 2>/dev/null; ./trial.sh $1 $2 ${3}b; }; \
  [ "${COMMIT:-0}" = 1 ] && (cd ../.. && git add -A testbed/v4/runs && git commit -qm "v4 trial $3" || true); }
for i in $(seq 1 $N); do for a in p1ctl indep safe; do one p1 $a p1_${a}_$i; done; done
for i in $(seq 1 $N); do for a in gamma uncapped cap10; do one p3 $a p3_${a}_$i; done; done
python3 analyze.py
