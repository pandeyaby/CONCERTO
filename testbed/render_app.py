#!/usr/bin/env python3
"""Render app manifests for campaign arms.

Modes:
  rq1          — sidecar local_ratelimit only (legacy RQ1). Args: R
  ac           — sidecar adaptive_concurrency pinned to L. Args: L
  twotier      — edge + sidecar local_ratelimit. Args: R_edge, R_side
  p3           — fixed 8 pods, HPA off, outlier detection, optional fault pod.
                 Args: policy in {none,maxej10,minhealth50,gamma}
"""
from __future__ import annotations

import argparse
import sys


def sidecar_ratelimit(burst: int, fill: int) -> str:
    return f"""              - name: envoy.filters.http.local_ratelimit
                typed_config:
                  "@type": type.googleapis.com/envoy.extensions.filters.http.local_ratelimit.v3.LocalRateLimit
                  stat_prefix: shed
                  token_bucket: {{max_tokens: {burst}, tokens_per_fill: {fill}, fill_interval: 0.1s}}
                  filter_enabled: {{runtime_key: e, default_value: {{numerator: 100, denominator: HUNDRED}}}}
                  filter_enforced: {{runtime_key: f, default_value: {{numerator: 100, denominator: HUNDRED}}}}"""


def sidecar_ac(limit: int) -> str:
    # Pin min_concurrency == max_concurrency_limit so the AC filter is a fixed
    # concurrency limiter on the AC rejection path (503), not a gradient study.
    return f"""              - name: envoy.filters.http.adaptive_concurrency
                typed_config:
                  "@type": type.googleapis.com/envoy.extensions.filters.http.adaptive_concurrency.v3.AdaptiveConcurrency
                  gradient_controller_config:
                    sample_rtt_percentile: {{value: 50}}
                    concurrency_limit_params:
                      max_concurrency_limit: {limit}
                      concurrency_update_interval: 0.1s
                    min_rtt_calc_params:
                      interval: 60s
                      request_count: 20
                      min_concurrency: {limit}
                      jitter: {{value: 0}}
                  enabled: {{default_value: {{numerator: 100, denominator: HUNDRED}}, runtime_key: ac}}"""


def edge_router_only() -> str:
    return """              http_filters: [{name: envoy.filters.http.router, typed_config: {"@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router}}]"""


def edge_with_ratelimit(burst: int, fill: int) -> str:
    return f"""              http_filters:
              - name: envoy.filters.http.local_ratelimit
                typed_config:
                  "@type": type.googleapis.com/envoy.extensions.filters.http.local_ratelimit.v3.LocalRateLimit
                  stat_prefix: edge_shed
                  token_bucket: {{max_tokens: {burst}, tokens_per_fill: {fill}, fill_interval: 0.1s}}
                  filter_enabled: {{runtime_key: ee, default_value: {{numerator: 100, denominator: HUNDRED}}}}
                  filter_enforced: {{runtime_key: ef, default_value: {{numerator: 100, denominator: HUNDRED}}}}
              - name: envoy.filters.http.router
                typed_config: {{"@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router}}"""


def outlier_block(max_ej: int) -> str:
    return f"""        outlier_detection:
          consecutive_5xx: 3
          interval: 2s
          base_ejection_time: 30s
          max_ejection_time: 30s
          max_ejection_percent: {max_ej}
          enforcing_consecutive_5xx: 100"""


def render(mode: str, **kw) -> str:
    replicas = kw.get("replicas", 2)
    hpa = kw.get("hpa", True)
    sidecar_filters = kw["sidecar_filters"]
    edge_http_filters = kw["edge_http_filters"]
    outlier = kw.get("outlier", "")
    fault_container = kw.get("fault_container", "")

    hpa_yaml = ""
    if hpa:
        hpa_yaml = """---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: {name: app, namespace: tb}
spec:
  scaleTargetRef: {apiVersion: apps/v1, kind: Deployment, name: app}
  minReplicas: 2
  maxReplicas: 8
  metrics:
  - type: Pods
    pods: {metric: {name: envoy_ok_rps}, target: {type: AverageValue, averageValue: "35"}}
"""

    # Optional second deployment that always fails (P3 faulty host).
    fault_yaml = ""
    if fault_container:
        fault_yaml = f"""---
apiVersion: v1
kind: ConfigMap
metadata: {{name: fault, namespace: tb}}
data:
  app.py: |
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(503); self.send_header("Content-Length","3"); self.end_headers(); self.wfile.write(b"err")
        def log_message(self,*a): pass
    ThreadingHTTPServer(("127.0.0.1", 9000), H).serve_forever()
  envoy.yaml: |
    admin: {{address: {{socket_address: {{address: 0.0.0.0, port_value: 9901}}}}}}
    static_resources:
      listeners:
      - address: {{socket_address: {{address: 0.0.0.0, port_value: 8080}}}}
        filter_chains:
        - filters:
          - name: envoy.filters.network.http_connection_manager
            typed_config:
              "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
              stat_prefix: ingress
              route_config: {{virtual_hosts: [{{name: a, domains: ["*"], routes: [{{match: {{prefix: "/"}}, route: {{cluster: app, timeout: 10s}}}}]}}]}}
              http_filters:
              - name: envoy.filters.http.router
                typed_config: {{"@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router}}
      clusters:
      - name: app
        type: STATIC
        connect_timeout: 1s
        load_assignment: {{cluster_name: app, endpoints: [{{lb_endpoints: [{{endpoint: {{address: {{socket_address: {{address: 127.0.0.1, port_value: 9000}}}}}}]}}]}}}}
---
apiVersion: apps/v1
kind: Deployment
metadata: {{name: fault, namespace: tb}}
spec:
  replicas: 1
  selector: {{matchLabels: {{app: app, role: fault}}}}
  template:
    metadata:
      labels: {{app: app, role: fault}}
      annotations: {{prometheus.io/scrape: "true", prometheus.io/port: "9901", prometheus.io/path: /stats/prometheus}}
    spec:
      containers:
      - name: app
        image: docker.io/library/python:3.12-alpine
        command: ["python","-u","/c/app.py"]
        volumeMounts: [{{name: c, mountPath: /c}}]
      - name: envoy
        image: docker.io/envoyproxy/envoy:v1.31.4
        args: ["-c","/c/envoy.yaml","--log-level","warn"]
        ports: [{{containerPort: 8080}}]
        readinessProbe: {{httpGet: {{path: /ready, port: 9901}}, periodSeconds: 2}}
        volumeMounts: [{{name: c, mountPath: /c}}]
      volumes: [{{name: c, configMap: {{name: fault}}}}]
"""

    return f"""apiVersion: v1
kind: ConfigMap
metadata: {{name: app, namespace: tb}}
data:
  app.py: |
    import time, threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    sem = threading.Semaphore(4)   # 4 workers x 80 ms = 50 req/s per pod
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            with sem: time.sleep(0.08)
            self.send_response(200); self.send_header("Content-Length","2"); self.end_headers(); self.wfile.write(b"ok")
        def log_message(self,*a): pass
    ThreadingHTTPServer(("127.0.0.1", 9000), H).serve_forever()
  envoy.yaml: |
    admin: {{address: {{socket_address: {{address: 0.0.0.0, port_value: 9901}}}}}}
    static_resources:
      listeners:
      - address: {{socket_address: {{address: 0.0.0.0, port_value: 8080}}}}
        filter_chains:
        - filters:
          - name: envoy.filters.network.http_connection_manager
            typed_config:
              "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
              stat_prefix: ingress
              route_config: {{virtual_hosts: [{{name: a, domains: ["*"], routes: [{{match: {{prefix: "/"}}, route: {{cluster: app, timeout: 10s}}}}]}}]}}
              http_filters:
{sidecar_filters}
              - name: envoy.filters.http.router
                typed_config: {{"@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router}}
      clusters:
      - name: app
        type: STATIC
        connect_timeout: 1s
        load_assignment: {{cluster_name: app, endpoints: [{{lb_endpoints: [{{endpoint: {{address: {{socket_address: {{address: 127.0.0.1, port_value: 9000}}}}}}]}}]}}}}
---
apiVersion: apps/v1
kind: Deployment
metadata: {{name: app, namespace: tb}}
spec:
  replicas: {replicas}
  selector: {{matchLabels: {{app: app, role: good}}}}
  template:
    metadata:
      labels: {{app: app, role: good}}
      annotations: {{prometheus.io/scrape: "true", prometheus.io/port: "9901", prometheus.io/path: /stats/prometheus}}
    spec:
      containers:
      - name: app
        image: docker.io/library/python:3.12-alpine
        command: ["python","-u","/c/app.py"]
        volumeMounts: [{{name: c, mountPath: /c}}]
      - name: envoy
        image: docker.io/envoyproxy/envoy:v1.31.4
        args: ["-c","/c/envoy.yaml","--log-level","warn"]
        ports: [{{containerPort: 8080}}]
        readinessProbe: {{httpGet: {{path: /ready, port: 9901}}, periodSeconds: 2}}
        volumeMounts: [{{name: c, mountPath: /c}}]
      volumes: [{{name: c, configMap: {{name: app}}}}]
---
apiVersion: v1
kind: Service
metadata: {{name: app, namespace: tb}}
spec:
  clusterIP: None
  selector: {{app: app}}
  ports: [{{port: 8080, targetPort: 8080}}]
{fault_yaml}---
apiVersion: v1
kind: ConfigMap
metadata: {{name: edge, namespace: tb}}
data:
  envoy.yaml: |
    admin: {{address: {{socket_address: {{address: 0.0.0.0, port_value: 9901}}}}}}
    static_resources:
      listeners:
      - address: {{socket_address: {{address: 0.0.0.0, port_value: 8080}}}}
        filter_chains:
        - filters:
          - name: envoy.filters.network.http_connection_manager
            typed_config:
              "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
              stat_prefix: edge
              route_config: {{virtual_hosts: [{{name: a, domains: ["*"], routes: [{{match: {{prefix: "/"}}, route: {{cluster: app, timeout: 10s}}}}]}}]}}
{edge_http_filters}
      clusters:
      - name: app
        type: STRICT_DNS
        dns_refresh_rate: 2s
        lb_policy: ROUND_ROBIN
        connect_timeout: 1s
        circuit_breakers: {{thresholds: [{{max_connections: 100000, max_pending_requests: 100000, max_requests: 100000}}]}}
{outlier}
        load_assignment: {{cluster_name: app, endpoints: [{{lb_endpoints: [{{endpoint: {{address: {{socket_address: {{address: app.tb.svc.cluster.local, port_value: 8080}}}}}}]}}]}}}}
---
apiVersion: apps/v1
kind: Deployment
metadata: {{name: edge, namespace: tb}}
spec:
  replicas: 1
  selector: {{matchLabels: {{app: edge}}}}
  template:
    metadata: {{labels: {{app: edge}}}}
    spec:
      containers:
      - name: envoy
        image: docker.io/envoyproxy/envoy:v1.31.4
        args: ["-c","/c/envoy.yaml","--log-level","warn"]
        volumeMounts: [{{name: c, mountPath: /c}}]
      volumes: [{{name: c, configMap: {{name: edge}}}}]
---
apiVersion: v1
kind: Service
metadata: {{name: edge, namespace: tb}}
spec:
  type: NodePort
  selector: {{app: edge}}
  ports: [{{port: 8080, targetPort: 8080, nodePort: 30080}}]
{hpa_yaml}"""


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["rq1", "ac", "twotier", "p1", "p3"])
    p.add_argument("--R", type=int, default=30, help="sidecar rate (rq1)")
    p.add_argument("--L", type=int, default=2, help="AC concurrency pin")
    p.add_argument("--R-edge", type=int, default=80)
    p.add_argument("--R-side", type=int, default=40)
    p.add_argument("--policy", default="none", choices=["none", "maxej10", "minhealth50", "gamma"])
    args = p.parse_args()

    if args.mode == "rq1":
        fill = max(1, args.R // 10)
        text = render(
            "rq1",
            sidecar_filters=sidecar_ratelimit(args.R, fill),
            edge_http_filters=edge_router_only(),
        )
    elif args.mode == "ac":
        text = render(
            "ac",
            sidecar_filters=sidecar_ac(args.L),
            edge_http_filters=edge_router_only(),
        )
    elif args.mode in ("twotier", "p1"):
        ef = max(1, args.R_edge // 10)
        sf = max(1, args.R_side // 10)
        text = render(
            args.mode,
            sidecar_filters=sidecar_ratelimit(args.R_side, sf),
            edge_http_filters=edge_with_ratelimit(args.R_edge, ef),
        )
    else:  # p3
        maxej = {"none": 100, "maxej10": 10, "minhealth50": 50, "gamma": 100}[args.policy]
        # 9 healthy + 1 fault = 10 endpoints (fits the 4-vCPU box). Percent caps:
        # 10% → 1 host, 50% → 5, 100% → all. Gamma stand-in = Γ-derived one-host
        # cap (eject the faulty host only); at N=10 this coincides with maxej10.
        if args.policy == "gamma":
            maxej = 10
        text = render(
            "p3",
            replicas=9,
            hpa=False,
            sidecar_filters=sidecar_ratelimit(200, 20),  # effectively off
            edge_http_filters=edge_router_only(),
            outlier=outlier_block(maxej),
            fault_container=True,
        )
    sys.stdout.write(text)


if __name__ == "__main__":
    main()
