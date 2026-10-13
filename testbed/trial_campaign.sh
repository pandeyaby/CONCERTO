#!/bin/bash
# usage:
#   trial_campaign.sh ac <L> <label>
#   trial_campaign.sh twotier <R_edge> <R_side> <label>
#   trial_campaign.sh p1 <R_edge> <R_side> <label>
#   trial_campaign.sh p3 <policy> <label>
#   trial_campaign.sh rq1 <R> <label>
set -e
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
ROOT=$(dirname "$0")
MODE=$1; shift
case "$MODE" in
  ac) L=$1; LABEL=$2; RENDER=(python3 "$ROOT/render_app.py" ac --L "$L") ;;
  twotier|p1) RE=$1; RS=$2; LABEL=$3; RENDER=(python3 "$ROOT/render_app.py" "$MODE" --R-edge "$RE" --R-side "$RS") ;;
  p3) POL=$1; LABEL=$2; RENDER=(python3 "$ROOT/render_app.py" p3 --policy "$POL") ;;
  rq1) R=$1; LABEL=$2; RENDER=(python3 "$ROOT/render_app.py" rq1 --R "$R") ;;
  *) echo "unknown mode $MODE"; exit 2 ;;
esac
D="$ROOT/runs/$LABEL"; mkdir -p "$D"
kubectl delete ns tb --ignore-not-found --wait=true >/dev/null 2>&1
kubectl create ns tb >/dev/null
"${RENDER[@]}" | kubectl apply -f - >/dev/null
kubectl -n tb rollout status deploy/app --timeout=180s >/dev/null
kubectl -n tb rollout status deploy/edge --timeout=180s >/dev/null
if kubectl -n tb get deploy fault >/dev/null 2>&1; then
  kubectl -n tb rollout status deploy/fault --timeout=180s >/dev/null
fi
sleep 5
# Warm custom metrics when HPA is present
if kubectl -n tb get hpa app >/dev/null 2>&1; then
  for i in $(seq 1 60); do
    kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1/namespaces/tb/pods/*/envoy_ok_rps" >/dev/null 2>&1 && break
    echo -n .
    vegeta attack -keepalive=false -rate=5 -duration=2s -targets=<(echo GET http://127.0.0.1:30080/) >/dev/null
  done
  echo
fi
if [ "$MODE" = "p3" ]; then
  ( while true; do
      echo "$(date +%s),$(kubectl -n tb get pods -l app=app --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | tr -d ' ')"
      sleep 5
    done ) > "$D/replicas.csv" & SP=$!
else
  ( while true; do
      echo "$(date +%s),$(kubectl -n tb get deploy app -o jsonpath='{.status.replicas}')"
      sleep 5
    done ) > "$D/replicas.csv" & SP=$!
fi
T="GET http://127.0.0.1:30080/"
if [ "$MODE" = "p3" ]; then
  echo "$T" | vegeta attack -keepalive=false -rate=200 -duration=180s -timeout=10s > "$D/v2.bin"
  : > "$D/v1.bin"
else
  echo "$T" | vegeta attack -keepalive=false -rate=50 -duration=60s -timeout=10s > "$D/v1.bin"
  echo "$T" | vegeta attack -keepalive=false -rate=160 -duration=480s -timeout=10s > "$D/v2.bin"
fi
kill $SP 2>/dev/null || true
wait $SP 2>/dev/null || true
if [ "$MODE" = "p3" ]; then
  EP=$(kubectl -n tb get pods -l app=edge -o jsonpath='{.items[0].metadata.name}')
  kubectl -n tb exec "$EP" -c envoy -- wget -qO- http://127.0.0.1:9901/clusters 2>/dev/null \
    | grep -E 'hostname|health_flags|success|eject' > "$D/clusters.txt" || true
fi
echo "mode=$MODE label=$LABEL done"
