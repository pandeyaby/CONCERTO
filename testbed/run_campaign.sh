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
  if [ -f "runs/$label/v2.bin" ] && [ -s "runs/$label/v2.bin" ]; then return 0; fi
  if [ -f "runs/${label}b/v2.bin" ] && [ -s "runs/${label}b/v2.bin" ]; then return 0; fi
  python3 -c "import json,sys; r=json.load(open('results_campaign.json')); sys.exit(0 if any(k==sys.argv[1] or k.startswith(sys.argv[1]+'_') or k==sys.argv[1]+'b' for k in r) else 1)" "$label" 2>/dev/null
}

run_once() {
  local label=$1; shift
  if is_complete "$label"; then
    echo "SKIP run $label (exists); ensuring committed"
    # Prefer committing the labelb artifact if that is what exists
    if [ ! -d "runs/$label" ] && [ -d "runs/${label}b" ]; then
      ./commit_trial.sh "${label}b" || true
      return 0
    fi
  else
    echo "=== RUN $* -> $label ==="
    "$@"
  fi
  ./commit_trial.sh "$label"
}

run() {
  local label=$1; shift
  if run_once "$label" "$@"; then
    return 0
  fi
  echo "INVALID $label — moving aside and retrying once as ${label}b"
  mkdir -p runs/invalid
  ts=$(date +%Y%m%d%H%M%S)
  mv "runs/$label" "runs/invalid/${label}_${ts}" || true
  local args=("$@")
  local last=$((${#args[@]} - 1))
  args[$last]="${label}b"
  if run_once "${label}b" "${args[@]}"; then
    return 0
  fi
  echo "FAILED $label after retry — continuing campaign"
  mkdir -p runs/invalid
  ts=$(date +%Y%m%d%H%M%S)
  mv "runs/${label}b" "runs/invalid/${label}b_${ts}" 2>/dev/null || true
  return 0
}

# E-AC
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
