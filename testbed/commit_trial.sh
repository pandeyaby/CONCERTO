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
# Validity: HPA arms need full phase2 + tight sampling; P3 is shorter.
if label.startswith("p3_"):
    ok = a["phase2_duration_s"] >= 170 and a.get("n", 0) >= 1000
else:
    ok = a["phase2_duration_s"] >= 470 and a["max_sample_gap_s"] <= 10
print(json.dumps({"label": label, "valid": ok, **a}, indent=2))
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
