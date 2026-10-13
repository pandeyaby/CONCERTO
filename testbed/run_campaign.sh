#!/bin/bash
# Run PREREG v3 campaign arms. Continues from existing runs/<label> dirs.
# Commits and pushes after EVERY completed valid trial.
set -e
ROOT=$(cd "$(dirname "$0")" && pwd)
cd "$ROOT"
chmod +x trial_campaign.sh commit_trial.sh
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

is_complete() {
  local label=$1
  [ -f "runs/$label/v2.bin" ] && [ -s "runs/$label/v2.bin" ]
}

run_once() {
  local label=$1; shift
  if is_complete "$label"; then
    echo "SKIP run $label (exists); ensuring committed"
  else
    echo "=== RUN $* -> $label ==="
    "$@"
  fi
  ./commit_trial.sh "$label"
}

run() {
  # Last CLI arg is the label for trial_campaign.sh; keep it in sync.
  local label=$1; shift
  if run_once "$label" "$@"; then
    return 0
  fi
  echo "INVALID $label — moving aside and retrying once as ${label}b"
  mkdir -p runs/invalid
  ts=$(date +%Y%m%d%H%M%S)
  mv "runs/$label" "runs/invalid/${label}_${ts}" || true
  # Replace trailing label arg with labelb for retry.
  local args=("$@")
  local last=$((${#args[@]} - 1))
  args[$last]="${label}b"
  run_once "${label}b" "${args[@]}"
}

# E-AC: 3 TRAP (L=2) + 3 REVERSE (L=6)
for i in 1 2 3; do
  run "ac_trap_$i" ./trial_campaign.sh ac 2 "ac_trap_$i"
  run "ac_reverse_$i" ./trial_campaign.sh ac 6 "ac_reverse_$i"
done

# E-two-tier
for i in 1 2 3; do
  run "tt_safe_$i" ./trial_campaign.sh twotier 200 40 "tt_safe_$i"
  run "tt_indep_$i" ./trial_campaign.sh twotier 80 40 "tt_indep_$i"
done

# E-P1 shared budget (edge 50 + side 25)
for i in 1 2 3; do
  run "p1_budget_$i" ./trial_campaign.sh p1 50 25 "p1_budget_$i"
done

# E-P3
for pol in none maxej10 minhealth50 gamma; do
  for i in 1 2 3; do
    run "p3_${pol}_$i" ./trial_campaign.sh p3 "$pol" "p3_${pol}_$i"
  done
done

python3 analyze.py
python3 verdicts_v3.py
echo CAMPAIGN DONE
