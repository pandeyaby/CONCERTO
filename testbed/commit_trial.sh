#!/bin/bash
# Analyze one completed trial label, merge into results_campaign.json, commit+push.
# usage: commit_trial.sh <label>
# Exit 3 = trial invalid. Exit 0 = trial accepted (even if push had to be retried).
set -e
ROOT=$(cd "$(dirname "$0")" && pwd)
cd "$ROOT"
LABEL=$1
[ -n "$LABEL" ] || { echo "usage: commit_trial.sh <label>"; exit 2; }
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

python3 - <<PY
import json, os, sys
from analyze import analyze
label = "$LABEL"
path = f"runs/{label}"
a = analyze(path)
rep_n = sum(1 for l in open(f"{path}/replicas.csv") if l.strip().split(",")[-1].isdigit())
if label.startswith("p3_"):
    ok = a["phase2_duration_s"] >= 170 and a.get("n", 0) >= 1000
elif a["phase2_duration_s"] >= 470 and a["max_sample_gap_s"] <= 10:
    ok = True
elif a["phase2_duration_s"] >= 470 and a["max_sample_gap_s"] <= 600 and rep_n >= 60 and a["final_replicas"] is not None:
    a["sampling"] = "degraded"
    ok = True
else:
    ok = False
print(json.dumps({"label": label, "valid": ok, "rep_n": rep_n, **a}, indent=2))
if not ok:
    sys.exit(3)
res = {}
if os.path.exists("results_campaign.json"):
    res = json.load(open("results_campaign.json"))
res[label] = a
json.dump(res, open("results_campaign.json", "w"), indent=1)
PY

REPO=$(cd "$ROOT/.." && pwd)
cd "$REPO"
git add "testbed/runs/$LABEL/replicas.csv" testbed/results_campaign.json
[ -f "testbed/runs/$LABEL/clusters.txt" ] && git add "testbed/runs/$LABEL/clusters.txt" || true
if git diff --cached --quiet; then
  echo "nothing new to commit for $LABEL"
else
  git commit -m "Testbed campaign: $LABEL valid"
fi

# Push with rebase-retry; never fail the trial over a push race.
push_ok=0
for attempt in 1 2 3 4; do
  if git push origin HEAD; then
    push_ok=1
    break
  fi
  echo "push attempt $attempt failed; fetch+rebase and retry"
  git fetch origin cursor/genesisgttestbed-campaign-ebe8
  git rebase origin/cursor/genesisgttestbed-campaign-ebe8 || {
    git rebase --abort 2>/dev/null || true
    # Prefer ours for results merge via manual combine
    git pull --no-rebase origin cursor/genesisgttestbed-campaign-ebe8 -X ours || true
  }
  sleep $((attempt * 4))
done
if [ "$push_ok" -ne 1 ]; then
  echo "WARNING: could not push $LABEL; trial data is committed locally"
fi
echo "COMMITTED $LABEL"
