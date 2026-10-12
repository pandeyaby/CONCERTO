#!/bin/bash
# usage: trial.sh <R per-pod req/s> <label>   -> writes runs/<label>/{vegeta.bin,replicas.csv}
set -e; export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
R=$1; L=$2; D=$(dirname $0)/runs/$L; mkdir -p $D
kubectl delete ns tb --ignore-not-found --wait=true >/dev/null 2>&1
kubectl create ns tb >/dev/null
F=$((R/10)); sed "s/__BURST__/$R/; s/__FILL__/$F/" $(dirname $0)/app.yaml.tpl | kubectl apply -f - >/dev/null
kubectl -n tb rollout status deploy/app --timeout=180s >/dev/null; kubectl -n tb rollout status deploy/edge --timeout=180s >/dev/null; sleep 5
for i in $(seq 1 60); do kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1/namespaces/tb/pods/*/envoy_ok_rps" >/dev/null 2>&1 && break; echo -n . ; vegeta attack -keepalive=false -rate=5 -duration=2s -targets=<(echo GET http://127.0.0.1:30080/) >/dev/null; done; echo
( while true; do echo "$(date +%s),$(kubectl -n tb get deploy app -o jsonpath='{.status.replicas}')"; sleep 5; done ) > $D/replicas.csv & SP=$!
T="GET http://127.0.0.1:30080/"
echo "$T" | vegeta attack -keepalive=false -rate=50 -duration=60s -timeout=10s > $D/v1.bin; echo "$T" | vegeta attack -keepalive=false -rate=160 -duration=480s -timeout=10s > $D/v2.bin
kill $SP
echo "R=$R label=$L done"
