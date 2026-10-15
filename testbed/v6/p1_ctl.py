"""Threshold-aware shared-budget controller (CONCERTO P1 as designed), external to Envoy.
Every 5 s:
  1. Read the edge's offered and shed rates (admin /stats) and the ready pods (kubectl).
  2. Severity s = shed/offered at the edge (0..1).
  3. Threshold constraint: no per-pod shedder may trip below the autoscaler's target. Each sidecar concurrency
     cap is set so its trip rate is >= (1+M)*TARGET, i.e. ceil((1+M)*TARGET*SVC), and never below the pod's
     natural concurrency (W).
  4. Budget allocation: the fleet admission budget B = n_ready * POD_CAP (req/s). Shedding authority beyond the
     sidecar guard goes to the edge (the fast actuator nearest the disturbance): edge cap = ceil(B*SVC*(1+H(s))),
     with headroom H(s) = 0.10 + 0.20*(1-s). At high severity, less headroom; at low severity, more slack.
     The per-pod admitted share B/n = POD_CAP stays >= TARGET, so the autoscaler sees demand above target.
Writes runtime keys circuit_breakers.app.default.max_{connections,requests} on the edge and on every sidecar.
Logs JSON lines."""
import json, math, subprocess, time, urllib.request
EDGE = "http://127.0.0.1:30902"; NS = "v6p1"
TARGET, M, SVC, W, POD_CAP = 25.0, 0.15, 0.109, 4, 36.8  # v6: IDENTICAL to v5 (same threshold-aware rule, no retuning)
def get(u): return urllib.request.urlopen(u, timeout=2).read().decode()
def post(u): urllib.request.urlopen(urllib.request.Request(u, method="POST"), timeout=2).read()
def stat(name):
    for l in get(EDGE + "/stats?filter=^" + name + "$").splitlines():
        k, _, v = l.partition(": ")
        if k == name: return int(v)
    return 0
def pods():
    out = subprocess.run(["kubectl", "-n", NS, "get", "pods", "-l", "app=app", "-o",
                          "jsonpath={range .items[*]}{.status.podIP} {.status.containerStatuses[*].ready}{\"\\n\"}{end}"],
                         capture_output=True, text=True, timeout=8).stdout
    return [l.split()[0] for l in out.splitlines() if l.strip() and "false" not in l]
def setcap(base, n):
    post(f"{base}/runtime_modify?circuit_breakers.app.default.max_connections={n}&circuit_breakers.app.default.max_requests={n}")
prev = None
while True:
    t0 = time.time()
    try:
        tot, ovf = stat("cluster.app.upstream_rq_total"), stat("cluster.app.upstream_cx_overflow") + stat("cluster.app.upstream_rq_pending_overflow")
        cur = (t0, tot + ovf, ovf)
        s = 0.0
        if prev:
            off = (cur[1] - prev[1]); shed = (cur[2] - prev[2]); s = shed / off if off > 0 else 0.0
        prev = cur
        ips = pods(); n = max(1, len(ips))
        side = max(W, math.ceil((1 + M) * TARGET * SVC))
        B = n * POD_CAP; H = 0.10 + 0.20 * (1 - s)
        edge = max(1, math.ceil(B * SVC * (1 + H)))
        setcap(EDGE, edge)
        for ip in ips:
            try: setcap(f"http://{ip}:9901", side)
            except Exception: pass
        print(json.dumps({"t": round(t0), "sev": round(s, 3), "pods": n, "edge_cap": edge, "side_cap": side}), flush=True)
    except Exception as e:
        print(json.dumps({"t": round(t0), "err": str(e)[:120]}), flush=True)
    time.sleep(max(0, 5 - (time.time() - t0)))
