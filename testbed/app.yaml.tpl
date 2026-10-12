apiVersion: v1
kind: ConfigMap
metadata: {name: app, namespace: tb}
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
    admin: {address: {socket_address: {address: 0.0.0.0, port_value: 9901}}}
    static_resources:
      listeners:
      - address: {socket_address: {address: 0.0.0.0, port_value: 8080}}
        filter_chains:
        - filters:
          - name: envoy.filters.network.http_connection_manager
            typed_config:
              "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
              stat_prefix: ingress
              route_config: {virtual_hosts: [{name: a, domains: ["*"], routes: [{match: {prefix: "/"}, route: {cluster: app, timeout: 10s}}]}]}
              http_filters:
              - name: envoy.filters.http.local_ratelimit
                typed_config:
                  "@type": type.googleapis.com/envoy.extensions.filters.http.local_ratelimit.v3.LocalRateLimit
                  stat_prefix: shed
                  token_bucket: {max_tokens: __BURST__, tokens_per_fill: __FILL__, fill_interval: 0.1s}
                  filter_enabled: {runtime_key: e, default_value: {numerator: 100, denominator: HUNDRED}}
                  filter_enforced: {runtime_key: f, default_value: {numerator: 100, denominator: HUNDRED}}
              - name: envoy.filters.http.router
                typed_config: {"@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router}
      clusters:
      - name: app
        type: STATIC
        connect_timeout: 1s
        load_assignment: {cluster_name: app, endpoints: [{lb_endpoints: [{endpoint: {address: {socket_address: {address: 127.0.0.1, port_value: 9000}}}}]}]}
---
apiVersion: apps/v1
kind: Deployment
metadata: {name: app, namespace: tb}
spec:
  replicas: 2
  selector: {matchLabels: {app: app}}
  template:
    metadata:
      labels: {app: app}
      annotations: {prometheus.io/scrape: "true", prometheus.io/port: "9901", prometheus.io/path: /stats/prometheus}
    spec:
      containers:
      - name: app
        image: docker.io/library/python:3.12-alpine
        command: ["python","-u","/c/app.py"]
        volumeMounts: [{name: c, mountPath: /c}]
      - name: envoy
        image: docker.io/envoyproxy/envoy:v1.31.4
        args: ["-c","/c/envoy.yaml","--log-level","warn"]
        ports: [{containerPort: 8080}]
        readinessProbe: {httpGet: {path: /ready, port: 9901}, periodSeconds: 2}
        volumeMounts: [{name: c, mountPath: /c}]
      volumes: [{name: c, configMap: {name: app}}]
---
apiVersion: v1
kind: Service
metadata: {name: app, namespace: tb}
spec:
  clusterIP: None
  selector: {app: app}
  ports: [{port: 8080, targetPort: 8080}]
---
# Edge Envoy: round-robins over pod sidecars via headless-service DNS.
# (The box kernel lacks the iptables 'statistic' match, so kube-proxy cannot load-balance a multi-endpoint Service.)
apiVersion: v1
kind: ConfigMap
metadata: {name: edge, namespace: tb}
data:
  envoy.yaml: |
    admin: {address: {socket_address: {address: 0.0.0.0, port_value: 9901}}}
    static_resources:
      listeners:
      - address: {socket_address: {address: 0.0.0.0, port_value: 8080}}
        filter_chains:
        - filters:
          - name: envoy.filters.network.http_connection_manager
            typed_config:
              "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
              stat_prefix: edge
              route_config: {virtual_hosts: [{name: a, domains: ["*"], routes: [{match: {prefix: "/"}, route: {cluster: app, timeout: 10s}}]}]}
              http_filters: [{name: envoy.filters.http.router, typed_config: {"@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router}}]
      clusters:
      - name: app
        type: STRICT_DNS
        dns_refresh_rate: 2s
        lb_policy: ROUND_ROBIN
        connect_timeout: 1s
        circuit_breakers: {thresholds: [{max_connections: 100000, max_pending_requests: 100000, max_requests: 100000}]}
        load_assignment: {cluster_name: app, endpoints: [{lb_endpoints: [{endpoint: {address: {socket_address: {address: app.tb.svc.cluster.local, port_value: 8080}}}}]}]}
---
apiVersion: apps/v1
kind: Deployment
metadata: {name: edge, namespace: tb}
spec:
  replicas: 1
  selector: {matchLabels: {app: edge}}
  template:
    metadata: {labels: {app: edge}}
    spec:
      containers:
      - name: envoy
        image: docker.io/envoyproxy/envoy:v1.31.4
        args: ["-c","/c/envoy.yaml","--log-level","warn"]
        volumeMounts: [{name: c, mountPath: /c}]
      volumes: [{name: c, configMap: {name: edge}}]
---
apiVersion: v1
kind: Service
metadata: {name: edge, namespace: tb}
spec:
  type: NodePort
  selector: {app: edge}
  ports: [{port: 8080, targetPort: 8080, nodePort: 30080}]
---
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
