"""v6 analysis (P1 setting B, PREREG v6). Load phase = ramp_*.bin + v2.bin (hold). Validity: load phase >= 470 s, wall-clock max sample gap <= 10 s.
Metrics: attain on the final 240 s (= the 200 req/s hold); p99 of 2xx in the first 120 s of the load phase (ramp 50..120 req/s)."""
import subprocess, csv, io, json, os, glob, statistics as st
def vrows(f):
    out = subprocess.run(["vegeta", "encode", "--to", "csv", f], capture_output=True, text=True).stdout
    return [(int(r[0]), int(r[1]), int(r[2])) for r in csv.reader(io.StringIO(out))]
def series(f):
    return [tuple(map(int, l.strip().split(","))) for l in open(f) if l.count(",") == 1 and l.strip().split(",")[1]]
def gap(s): return max([b[0] - a[0] for a, b in zip(s, s[1:])] or [999])
def p99(xs): xs = sorted(xs); return xs[int(0.99 * (len(xs) - 1))] / 1e6 if xs else None
def a_p1(d):
    rows = [r for f in sorted(glob.glob(f"{d}/ramp_*.bin")) + [f"{d}/v2.bin"] for r in vrows(f)]; t0 = min(r[0] for r in rows); t1 = max(r[0] for r in rows)
    win = [r for r in rows if r[0] >= t1 - 240e9]; early = [r for r in rows if r[0] <= t0 + 120e9]
    rep = series(f"{d}/replicas.csv")
    return {"valid": (t1 - t0) / 1e9 >= 470 and gap(rep) <= 10, "dur": round((t1 - t0) / 1e9), "gap": gap(rep),
            "attain": round(sum(r[1] == 200 for r in win) / len(win), 4), "final_replicas": rep[-1][1] if rep else None,
            "p99_ms_first120": round(p99([r[2] for r in early if r[1] == 200]), 1)}
def main():
    R = {}
    for k in sorted(os.listdir("runs")):
        try: R[k] = a_p1(f"runs/{k}")
        except Exception as e: R[k] = {"valid": False, "error": str(e)[:80]}
    V = {k: v for k, v in R.items() if v.get("valid") and k.startswith("p1_")}
    arm = lambda p: [v for k, v in V.items() if k.startswith(p + "_")]
    m = lambda p, f: st.mean(x[f] for x in arm(p))
    out = {"trials": R, "n_valid": {a: len(arm(a)) for a in ("p1_indep", "p1_p1ctl", "p1_safe")}}; ver = {}
    if all(len(arm(a)) >= 5 for a in ("p1_indep", "p1_p1ctl", "p1_safe")):
        c = arm("p1_p1ctl"); ver["W0"] = sum(x["final_replicas"] >= 7 for x in arm("p1_safe")) >= 4
        out["means"] = {a: {f: round(m(a, f), 4) for f in ("attain", "final_replicas", "p99_ms_first120")} for a in ("p1_indep", "p1_p1ctl", "p1_safe")}
        vv = {"V1": m("p1_p1ctl", "attain") >= m("p1_indep", "attain") + 0.25,
              "V2": all(x["final_replicas"] >= 6 for x in c),
              "V3": m("p1_p1ctl", "attain") >= m("p1_safe", "attain") - 0.05,
              "V4": m("p1_p1ctl", "p99_ms_first120") <= 0.8 * m("p1_safe", "p99_ms_first120")}
        for k, v in vv.items(): ver[k] = v if ver["W0"] else "INCONCLUSIVE"
    else:
        ver = {k: "INCONCLUSIVE" for k in ("W0", "V1", "V2", "V3", "V4")}
    out["verdicts"] = {k: ("PASS" if v else "FAIL") if not isinstance(v, str) else v for k, v in ver.items()}
    print(json.dumps(out, indent=1)); json.dump(out, open("results_v6.json", "w"), indent=1)
if __name__ == "__main__": main()
