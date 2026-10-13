#!/bin/bash
# Resume remaining v4 trials after stop/clean-rerun. Same rules as run_all.sh.
# Remaining: p1_p1ctl_3, p1_indep_3, p1_safe_3, all P3 (N=3).
set -e
cd "$(dirname "$0")"
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
N=${N:-3}
cleanup_between() {
  pkill -f '[p]1_ctl.py' 2>/dev/null || true
  pkill -f '[g]amma_ctl.py' 2>/dev/null || true
  pkill -f '[s]ample_replicas.py' 2>/dev/null || true
  pkill -f '[s]ample_ejected.py' 2>/dev/null || true
  pkill -f '[v]egeta attack' 2>/dev/null || true
  sleep 1
  stray=$(pgrep -af '[p]1_ctl.py|[g]amma_ctl.py|[s]ample_replicas.py|[s]ample_ejected.py|[v]egeta attack' 2>/dev/null || true)
  if [ -n "$stray" ]; then
    echo "FATAL: stray processes after cleanup:" >&2
    echo "$stray" >&2
    exit 1
  fi
}
one() {
  cleanup_between
  echo "=== START $* $(date -u -Iseconds) ==="
  ./trial.sh "$@"
  v=$(python3 -c "import analyze as a,sys;print((a.a_p1 if '$1'=='p1' else a.a_p3)('runs/$3')['valid'])" 2>/dev/null)
  echo "valid=$v label=$3"
  [ "$v" = True ] || { mv runs/$3 runs/invalid_$3 2>/dev/null; cleanup_between; ./trial.sh $1 $2 ${3}b; }
  cleanup_between
  [ "${COMMIT:-0}" = 1 ] && (cd ../.. && git add -A testbed/v4/runs testbed/v4/run_all.log && git commit -qm "v4 trial $3" && git push -u origin HEAD || true)
  echo "=== DONE $3 $(date -u -Iseconds) ==="
}
cleanup_between
# P1 remaining (round 3); p1_p1ctl_3 from scratch (aborted_* retained separately)
one p1 p1ctl p1_p1ctl_3
one p1 indep p1_indep_3
one p1 safe p1_safe_3
# All P3
for i in $(seq 1 $N); do for a in gamma uncapped cap10; do one p3 $a p3_${a}_$i; done; done
python3 analyze.py | tee results_v4.json.tmp
# analyze.py already writes results_v4.json; keep tee copy for log
cp -f results_v4.json results_v4.json.bak 2>/dev/null || true
[ "${COMMIT:-0}" = 1 ] && (cd ../.. && git add -A testbed/v4 && git commit -qm "v4 campaign: final analyze after resume" && git push -u origin HEAD || true)
echo RESUME_EXIT:0
