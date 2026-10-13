#!/bin/bash
# usage: trial.sh p1 <indep|p1ctl|safe> <label>   |   trial.sh p3 <uncapped|cap10|gamma> <label>
# Writes runs/<label>/. Requires setup.sh (k3s, prometheus + adapter, vegeta).
set -e; export KUBECONFIG=/etc/rancher/k3s/k3s.yaml; cd "$(dirname "$0")"
EXP=$1; ARM=$2; L=$3; D=runs/$L; rm -rf "$D"; mkdir -p "$D"; CTL=""
sampler() { ( while true; do r=$(timeout 8 kubectl -n $1 get deploy app -o jsonpath='{.status.replicas}' 2>/dev/null) && [ -n "$r" ] && echo "$(date +%s),$r"; sleep 5; done ) > "$D/replicas.csv" & SP=$!; }
if [ "$EXP" = p1 ]; then
  NS=v4p1; case $ARM in indep|p1ctl) SIDE=2; EDGE=8;; safe) SIDE=6; EDGE=1000;; *) exit 2;; esac
  kubectl delete ns $NS --ignore-not-found --wait=true >/dev/null 2>&1; kubectl create ns $NS >/dev/null
  sed "s/__SIDE__/$SIDE/g; s/__EDGE__/$EDGE/g" p1.yaml.tpl | kubectl apply -f - >/dev/null
  kubectl -n $NS rollout status deploy/app --timeout=300s >/dev/null; kubectl -n $NS rollout status deploy/edge --timeout=120s >/dev/null; sleep 5
  for i in $(seq 1 90); do kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1/namespaces/$NS/pods/*/envoy_ok_rps" >/dev/null 2>&1 && break; echo "GET http://127.0.0.1:30280/" | vegeta attack -rate=5 -duration=2s >/dev/null; done
  [ $ARM = p1ctl ] && { python3 p1_ctl.py > "$D/ctl.log" 2>&1 & CTL=$!; }
  sampler $NS; T="GET http://127.0.0.1:30280/"
  echo "$T" | vegeta attack -keepalive=false -rate=50 -duration=60s -timeout=10s > "$D/v1.bin"
  echo "$T" | vegeta attack -keepalive=false -rate=160 -duration=480s -timeout=10s > "$D/v2.bin"
else
  NS=v4p3; case $ARM in uncapped|gamma) M=100;; cap10) M=10;; *) exit 2;; esac
  kubectl delete ns $NS --ignore-not-found --wait=true >/dev/null 2>&1; kubectl create ns $NS >/dev/null
  sed "s/__MAXEJ__/$M/" p3_pool.yaml.tpl | kubectl apply -f - >/dev/null
  kubectl -n $NS rollout status deploy/app --timeout=300s >/dev/null; kubectl -n $NS rollout status deploy/edge --timeout=120s >/dev/null; sleep 10
  IPS=$(kubectl -n $NS get pods -l app=app -o jsonpath='{.items[*].status.podIP}'); TOT=0
  for ip in $IPS; do c=$(curl -s -m2 http://$ip:9000/cap); echo "$ip,$c" >> "$D/caps.csv"; TOT=$(python3 -c "print($TOT+$c)"); done
  F=$(echo $IPS | tr ' ' '\n' | sort | head -1); curl -s -m2 http://$F:9000/fault >/dev/null; echo "$F" > "$D/faulty.txt"
  RATE=$(python3 -c "print(int(0.90*$TOT))"); echo $RATE > "$D/rate.txt"
  [ $ARM = gamma ] && { python3 gamma_ctl.py > "$D/ctl.log" 2>&1 & CTL=$!; }
  ( while true; do echo "$(date +%s),$(curl -s -m2 http://127.0.0.1:30903/clusters | grep -c failed_outlier_check)"; sleep 5; done ) > "$D/ejected.csv" & SP=$!
  echo "GET http://127.0.0.1:30380/" | vegeta attack -keepalive=false -rate=$RATE -duration=300s -timeout=10s > "$D/v2.bin"
  curl -s http://127.0.0.1:30903/stats | grep -E "outlier_detection\.(ejections_enforced_total|ejections_overflow)" > "$D/od_stats.txt" || true
  curl -s http://127.0.0.1:30903/clusters | grep -E "health_flags" > "$D/clusters_end.txt" || true
fi
kill $SP 2>/dev/null || true; [ -n "$CTL" ] && kill $CTL 2>/dev/null || true
echo "$EXP $ARM $L done"
