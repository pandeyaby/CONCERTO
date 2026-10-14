#!/bin/bash
# Full v4 campaign, interleaved arms; reruns an invalid trial once as <label>b. Commit after each trial if COMMIT=1.
cd "$(dirname "$0")"; N=${N:-3}
# Kill any leftover controllers/samplers/load gens between trials (NOTES #6/#7).
# Bracket trick in patterns avoids pgrep matching its own command line.
cleanup_between() {
  pkill -f '[p]1_ctl.py' 2>/dev/null || true
  pkill -f '[g]amma_ctl.py' 2>/dev/null || true
  pkill -f '[s]ample_replicas.py' 2>/dev/null || true
  pkill -f '[s]ample_ejected.py' 2>/dev/null || true
  pkill -f '[v]egeta attack' 2>/dev/null || true
  sleep 1
  # Fail hard if anything is still alive — do not start the next trial contaminated.
  stray=$(pgrep -af '[p]1_ctl.py|[g]amma_ctl.py|[s]ample_replicas.py|[s]ample_ejected.py|[v]egeta attack' 2>/dev/null || true)
  if [ -n "$stray" ]; then
    echo "FATAL: stray processes after cleanup:" >&2
    echo "$stray" >&2
    exit 1
  fi
}
one() {
  cleanup_between
  ./trial.sh "$@"
  v=$(python3 -c "import analyze as a,sys;print((a.a_p1 if '$1'=='p1' else a.a_p3)('runs/$3')['valid'])" 2>/dev/null)
  [ "$v" = True ] || { mv runs/$3 runs/invalid_$3 2>/dev/null; cleanup_between; ./trial.sh $1 $2 ${3}b; }
  cleanup_between
  [ "${COMMIT:-0}" = 1 ] && (cd ../.. && git add -A testbed/v4/runs && git commit -qm "v4 trial $3" && git push -u origin HEAD || true)
}
cleanup_between
for i in $(seq 1 $N); do for a in p1ctl indep safe; do one p1 $a p1_${a}_$i; done; done
for i in $(seq 1 $N); do for a in gamma uncapped cap10; do one p3 $a p3_${a}_$i; done; done
python3 analyze.py
