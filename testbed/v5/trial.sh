#!/bin/bash
# v5 P1 only. usage: trial.sh <indep|p1ctl|safe> <label>. Writes runs/<label>/. Requires ../setup.sh.
# Replica sampler uses WALL-CLOCK seconds (date +%s), as pre-registered in PREREG v5.
set -e; export KUBECONFIG=/etc/rancher/k3s/k3s.yaml; cd "$(dirname "$0")"
ARM=$1; L=$2; D=runs/$L; rm -rf "$D"; mkdir -p "$D"; CTL=""; NS=v5p1
cleanup() { pkill -f "p1_ctl.py" 2>/dev/null || true; pkill -x vegeta 2>/dev/null || true; pkill -f "v5_sampler" 2>/dev/null || true; }
cleanup; sleep 2; pgrep -fa "p1_ctl.py|vegeta attack" > "$D/preflight_procs.txt" && { echo "stray processes"; exit 3; } || true
case $ARM in indep|p1ctl) SIDE=2; EDGE=8;; safe) SIDE=6; EDGE=1000;; *) exit 2;; esac
kubectl delete ns $NS --ignore-not-found --wait=true >/dev/null 2>&1; kubectl create ns $NS >/dev/null
sed "s/__SIDE__/$SIDE/g; s/__EDGE__/$EDGE/g" p1.yaml.tpl | kubectl apply -f - >/dev/null
kubectl -n $NS rollout status deploy/app --timeout=300s >/dev/null; kubectl -n $NS rollout status deploy/edge --timeout=120s >/dev/null; sleep 5
for i in $(seq 1 90); do kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1/namespaces/$NS/pods/*/envoy_ok_rps" >/dev/null 2>&1 && break; echo "GET http://127.0.0.1:30280/" | vegeta attack -rate=5 -duration=2s >/dev/null; done
[ $ARM = p1ctl ] && { python3 p1_ctl.py > "$D/ctl.log" 2>&1 & CTL=$!; }
( exec -a v5_sampler bash -c "while true; do r=\$(timeout 8 kubectl -n $NS get deploy app -o jsonpath='{.status.replicas}' 2>/dev/null) && [ -n \"\$r\" ] && echo \"\$(date +%s),\$r\"; sleep 5; done" ) > "$D/replicas.csv" & SP=$!
T="GET http://127.0.0.1:30280/"
echo "$T" | vegeta attack -keepalive=false -rate=50 -duration=60s -timeout=10s > "$D/v1.bin"
echo "$T" | vegeta attack -keepalive=false -rate=160 -duration=480s -timeout=10s > "$D/v2.bin"
kill $SP 2>/dev/null || true; [ -n "$CTL" ] && kill $CTL 2>/dev/null || true; cleanup
kubectl -n $NS get hpa app -o yaml > "$D/hpa_end.yaml" 2>/dev/null || true
echo "$ARM $L done"
