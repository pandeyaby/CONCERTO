#!/bin/bash
# v5 campaign: N=5 per arm, interleaved p1ctl,indep,safe. An invalid trial is renamed invalid_<label> and rerun
# as <label>b, then <label>c (max 2 reruns per slot). COMMIT=1 commits after each trial.
cd "$(dirname "$0")"; N=${N:-5}
valid() { python3 -c "import analyze as a;print(a.a_p1('runs/$1')['valid'])" 2>/dev/null; }
one() { for s in "" b c; do ./trial.sh $1 $2$s; [ "$(valid $2$s)" = True ] && break; mv runs/$2$s runs/invalid_$2$s; done
  [ "${COMMIT:-0}" = 1 ] && (cd ../.. && git add -A testbed/v5/runs && git commit -qm "v5 trial $2" || true); }
for i in $(seq 1 $N); do for a in p1ctl indep safe; do one $a p1_${a}_$i; done; done
python3 analyze.py
