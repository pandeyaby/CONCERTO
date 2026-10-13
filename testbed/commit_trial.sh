#!/bin/bash
# Analyze one completed trial label, merge into results_campaign.json, commit+push.
# usage: commit_trial.sh <label>
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
# Validity: vegeta window must be complete. Replica sampling prefers <=10s gaps
# (RQ1 bar); under API stalls we accept degraded sampling if enough points remain
# and the gap is bounded, so attainment-primary arms are not discarded.
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
# clusters.txt for P3 if present
[ -f "testbed/runs/$LABEL/clusters.txt" ] && git add "testbed/runs/$LABEL/clusters.txt" || true
git add testbed/fill_campaign_paper.py testbed/run_campaign.sh testbed/commit_trial.sh testbed/.gitignore 2>/dev/null || true
if git diff --cached --quiet; then
  echo "nothing new to commit for $LABEL"
else
  git commit -m "Testbed campaign: $LABEL valid"
  git push origin HEAD
fi
echo "COMMITTED $LABEL"
