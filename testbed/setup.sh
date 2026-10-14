#!/bin/bash
# Reproducible $0 testbed bring-up on a box without Docker (k3s embedded containerd).
set -e; export HELM_KUBECONTEXT=
TESTBED_DIR=$(dirname "$(readlink -f "$0")")
cd /tmp
curl -sL -o k3s https://github.com/k3s-io/k3s/releases/download/v1.31.4%2Bk3s1/k3s && chmod +x k3s && sudo mv k3s /usr/local/bin/ && sudo ln -sf /usr/local/bin/k3s /usr/local/bin/kubectl
curl -sL https://github.com/tsenart/vegeta/releases/download/v12.12.0/vegeta_12.12.0_linux_amd64.tar.gz | tar xz vegeta && sudo mv vegeta /usr/local/bin
curl -sL https://get.helm.sh/helm-v3.16.3-linux-amd64.tar.gz | tar xz && sudo mv linux-amd64/helm /usr/local/bin
# box kernel: overlayfs and vxlan unavailable -> native snapshotter + host-gw
(sudo nohup k3s server --disable traefik --snapshotter native --flannel-backend host-gw --write-kubeconfig-mode 644 >/tmp/k3s.log 2>&1 &)
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
until kubectl get nodes 2>/dev/null | grep -q " Ready"; do sleep 5; done
for i in docker.io/envoyproxy/envoy:v1.31.4 docker.io/library/python:3.12-alpine; do sudo k3s ctr images pull $i >/dev/null; done
helm repo add pc https://prometheus-community.github.io/helm-charts >/dev/null; helm repo update >/dev/null
helm install prom pc/prometheus -n mon --create-namespace --set alertmanager.enabled=false --set prometheus-pushgateway.enabled=false --set kube-state-metrics.enabled=false --set prometheus-node-exporter.enabled=false --set server.persistentVolume.enabled=false --set server.global.scrape_interval=5s --set server.global.scrape_timeout=4s >/dev/null 2>&1
helm install adapter pc/prometheus-adapter -n mon -f "$TESTBED_DIR/adapter-values.yaml"
kubectl -n mon rollout status deploy/prom-prometheus-server --timeout=300s
echo SETUP OK
