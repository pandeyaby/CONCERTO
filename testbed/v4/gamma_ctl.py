"""Gamma-gated ejection controller for Envoy (external, no Envoy modification).
Every 2 s: read per-host request counters and ejection flags from the admin /clusters endpoint and capacities from
each pod's /cap. Then set the runtime key outlier_detection.max_ejection_percent so that one more ejection is
admitted only if some currently-failing, non-ejected host has projected Gamma < 1, or is effectively dead
(success < 10%: its traffic is already lost, so moving it costs nothing). That dead-host exception is a disclosed
design choice beyond the PREREG v3 wording. Logs every decision to stdout as JSON."""
import json, math, sys, time, urllib.request
ADMIN = "http://127.0.0.1:30903"
def get(u, t=2): return urllib.request.urlopen(u, timeout=t).read().decode()
caps = {}; prev = {}
def hosts():
    h = {}
    for line in get(ADMIN + "/clusters").splitlines():
        p = line.split("::")
        if len(p) < 4 or p[0] != "app" or ":" not in p[1]: continue
        ip = p[1].split(":")[0]; d = h.setdefault(ip, {"ej": False})
        if p[2] in ("rq_success", "rq_error", "rq_total"): d[p[2]] = int(p[3])
        if p[2] == "health_flags": d["ej"] = "failed_outlier_check" in p[3]
    return h
pct = 100
while True:
    t0 = time.time()
    try:
        h = hosts(); n = len(h)
        for ip in h:
            if ip not in caps:
                try: caps[ip] = float(get(f"http://{ip}:9000/cap", 1))
                except Exception: caps[ip] = 50.0
        rate = {}
        for ip, d in h.items():
            p = prev.get(ip, d); dt = 2.0
            tot = d.get("rq_total", 0) - p.get("rq_total", 0); ok = d.get("rq_success", 0) - p.get("rq_success", 0)
            rate[ip] = (tot / dt, ok / max(tot, 1))
        prev = h
        alive = [ip for ip in h if not h[ip]["ej"]]; ej = n - len(alive)
        cands = [ip for ip in alive if rate[ip][1] < 0.99 and rate[ip][0] > 0]
        allow = False; why = []
        for j in cands:
            if rate[j][1] < 0.10: allow = True; why.append((j, "dead")); continue
            surv = [i for i in alive if i != j]
            share = rate[j][0] / max(len(surv), 1)
            g = sum(1 for i in surv if rate[i][0] + share > caps[i])
            why.append((j, g))
            if g < 1: allow = True
        # Envoy refuses an ejection when (ejected+1)/n*100 > max_ejection_percent
        new = min(100, math.ceil((ej + 1) * 100 / n)) if allow else max(0, (ej * 100) // n)
        if new != pct:
            urllib.request.urlopen(urllib.request.Request(ADMIN + f"/runtime_modify?outlier_detection.max_ejection_percent={new}", method="POST"), timeout=2)
            pct = new
        print(json.dumps({"t": round(t0), "ejected": ej, "cands": why, "max_ej_pct": pct}), flush=True)
    except Exception as e:
        print(json.dumps({"t": round(t0), "err": str(e)[:100]}), flush=True)
    time.sleep(max(0, 2 - (time.time() - t0)))
