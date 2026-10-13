apiVersion: v1
kind: ConfigMap
metadata: {name: pool, namespace: v4p3}
data:
  app.py: |
    import time, threading, socket, hashlib
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    W = [3, 4, 5][int(hashlib.md5(socket.gethostname().encode()).hexdigest(), 16) % 3]  # 37.5/50/62.5 req/s
    sem = threading.Semaphore(W); lock = threading.Lock(); st = {"inflight": 0, "fault": False}
    class H(BaseHTTPRequestHandler):
        def r(self, code, body=b"ok"):
            self.send_response(code); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
        def do_GET(self):
            if self.path == "/cap": return self.r(200, str(W * 12.5).encode())
            if self.path == "/fault": st["fault"] = True; return self.r(200)
            if st["fault"]: return self.r(503)
            with lock:
                if st["inflight"] >= W + 8: return self.r(503)
                st["inflight"] += 1
            try:
                with sem: time.sleep(0.08)
                self.r(200)
            finally:
                with lock: st["inflight"] -= 1
        def log_message(self, *a): pass
    ThreadingHTTPServer(("0.0.0.0", 9000), H).serve_forever()
  envoy.yaml: |
    admin: {address: {socket_address: {address: 0.0.0.0, port_value: 9901}}}
    layered_runtime: {layers: [{name: static, static_layer: {}}, {name: admin, admin_layer: {}}]}
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
        dns_refresh_rate: 5s
        lb_policy: ROUND_ROBIN
        connect_timeout: 1s
        common_lb_config: {healthy_panic_threshold: {value: 50}}
        circuit_breakers: {thresholds: [{max_connections: 100000, max_pending_requests: 100000, max_requests: 100000}]}
        outlier_detection: {consecutive_5xx: 5, interval: 2s, base_ejection_time: 30s, max_ejection_percent: __MAXEJ__}
        load_assignment: {cluster_name: app, endpoints: [{lb_endpoints: [{endpoint: {address: {socket_address: {address: app.v4p3.svc.cluster.local, port_value: 9000}}}}]}]}
---
apiVersion: apps/v1
kind: Deployment
metadata: {name: app, namespace: v4p3}
spec:
  replicas: 10
  selector: {matchLabels: {app: app}}
  template:
    metadata: {labels: {app: app}}
    spec:
      containers:
      - name: app
        image: docker.io/library/python:3.12-alpine
        command: ["python", "-u", "/c/app.py"]
        readinessProbe: {httpGet: {path: /cap, port: 9000}, periodSeconds: 2}
        volumeMounts: [{name: c, mountPath: /c}]
      volumes: [{name: c, configMap: {name: pool}}]
---
apiVersion: v1
kind: Service
metadata: {name: app, namespace: v4p3}
spec: {clusterIP: None, selector: {app: app}, ports: [{port: 9000, targetPort: 9000}]}
---
apiVersion: apps/v1
kind: Deployment
metadata: {name: edge, namespace: v4p3}
spec:
  replicas: 1
  selector: {matchLabels: {app: edge}}
  template:
    metadata: {labels: {app: edge}}
    spec:
      containers:
      - name: envoy
        image: docker.io/envoyproxy/envoy:v1.31.4
        args: ["-c", "/c/envoy.yaml", "--log-level", "warn"]
        volumeMounts: [{name: c, mountPath: /c}]
      volumes: [{name: c, configMap: {name: pool}}]
---
apiVersion: v1
kind: Service
metadata: {name: edge, namespace: v4p3}
spec:
  type: NodePort
  selector: {app: edge}
  ports: [{name: http, port: 8080, targetPort: 8080, nodePort: 30380}, {name: admin, port: 9901, targetPort: 9901, nodePort: 30903}]
