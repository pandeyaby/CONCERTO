#!/bin/bash
# usage: trial.sh <arm: uncapped|cap10|gamma> <label>
set -e; export KUBECONFIG=/etc/rancher/k3s/k3s.yaml; cd $(dirname $0)
ARM=$1; L=$2; D=runs/$L; mkdir -p $D
M=100; [ $ARM = cap10 ] && M=10
kubectl delete ns p3 --ignore-not-found --wait=true >/dev/null 2>&1; kubectl create ns p3 >/dev/null
sed "s/__MAXEJ__/$M/" pool.yaml.tpl | kubectl apply -f - >/dev/null
kubectl -n p3 rollout status deploy/app --timeout=300s >/dev/null; kubectl -n p3 rollout status deploy/edge --timeout=120s >/dev/null; sleep 10
IPS=$(kubectl -n p3 get pods -l app=app -o jsonpath='{.items[*].status.podIP}')
TOT=0; for ip in $IPS; do c=$(curl -s -m2 http://$ip:9000/cap); echo "$ip,$c" >> $D/caps.csv; TOT=$(python3 -c "print($TOT+$c)"); done
F=$(echo $IPS | tr ' ' '\n' | sort | head -1); curl -s -m2 http://$F:9000/fault >/dev/null; echo "$F" > $D/faulty.txt
RATE=$(python3 -c "print(int(0.85*$TOT))"); echo $RATE > $D/rate.txt
[ $ARM = gamma ] && { python3 gamma_ctl.py > $D/gamma.log 2>&1 & GP=$!; }
( while true; do echo "$(date +%s),$(curl -s -m2 http://127.0.0.1:30901/clusters | grep -c failed_outlier_check)"; sleep 5; done ) > $D/ejected.csv & SP=$!
echo "GET http://127.0.0.1:30180/" | vegeta attack -keepalive=false -rate=$RATE -duration=300s -timeout=10s > $D/v.bin
kill $SP; [ -n "$GP" ] && kill $GP || true
curl -s http://127.0.0.1:30901/clusters | grep -E "failed_outlier_check|rq_success|rq_error" > $D/clusters_end.txt
echo "$ARM $L done rate=$RATE"
