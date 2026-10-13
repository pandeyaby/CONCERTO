"""v4 analysis. Validity: load phase >= 470 s (P1) or >= 290 s (P3), max sample gap <= 10 s (original rule, primary)."""
import subprocess, csv, io, json, os, statistics as st
def vrows(f):
    out = subprocess.run(["vegeta", "encode", "--to", "csv", f], capture_output=True, text=True).stdout
    return [(int(r[0]), int(r[1]), int(r[2])) for r in csv.reader(io.StringIO(out))]
def series(f):
    return [tuple(map(int, l.strip().split(","))) for l in open(f) if l.count(",") == 1 and l.strip().split(",")[1]]
def gap(s): return max([b[0] - a[0] for a, b in zip(s, s[1:])] or [999])
def p99(xs): xs = sorted(xs); return xs[int(0.99 * (len(xs) - 1))] / 1e6 if xs else None
def a_p1(d):
    rows = vrows(f"{d}/v2.bin"); t0 = min(r[0] for r in rows); t1 = max(r[0] for r in rows)
    win = [r for r in rows if r[0] >= t1 - 240e9]; early = [r for r in rows if r[0] <= t0 + 120e9]
    rep = series(f"{d}/replicas.csv")
    return {"valid": (t1 - t0) / 1e9 >= 470 and gap(rep) <= 10, "dur": round((t1 - t0) / 1e9), "gap": gap(rep),
            "attain": round(sum(r[1] == 200 for r in win) / len(win), 4), "final_replicas": rep[-1][1] if rep else None,
            "p99_ms_first120": round(p99([r[2] for r in early if r[1] == 200]), 1)}
def a_p3(d):
    rows = vrows(f"{d}/v2.bin"); t0 = min(r[0] for r in rows); t1 = max(r[0] for r in rows)
    win = [r for r in rows if r[0] >= t1 - 180e9]; ej = series(f"{d}/ejected.csv")
    fault = open(f"{d}/faulty.txt").read().strip(); endc = open(f"{d}/clusters_end.txt").read()
    return {"valid": (t1 - t0) / 1e9 >= 290 and gap(ej) <= 10, "dur": round((t1 - t0) / 1e9), "gap": gap(ej),
            "goodput": round(sum(r[1] == 200 for r in win) / len(win), 4), "max_ejected": max(e for _, e in ej),
            "faulty_ejected_end": f"{fault}:9000::health_flags::/failed_outlier_check" in endc}
def main():
    R = {}
    for k in sorted(os.listdir("runs")):
        d = f"runs/{k}"
        try: R[k] = a_p1(d) if k.startswith("p1_") else a_p3(d)
        except Exception as e: R[k] = {"valid": False, "error": str(e)[:80]}
    V = {k: v for k, v in R.items() if v.get("valid")}
    arm = lambda p: [v for k, v in V.items() if k.startswith(p + "_")]
    m = lambda p, f: st.mean(x[f] for x in arm(p)) if arm(p) else None
    out = {"trials": R}; ver = {}
    if all(len(arm(a)) >= 3 for a in ("p1_indep", "p1_p1ctl", "p1_safe")):
        c, i, s = arm("p1_p1ctl"), m("p1_indep", "attain"), m("p1_safe", "attain")
        ver["V1"] = m("p1_p1ctl", "attain") >= i + 0.25
        ver["V2"] = all(x["final_replicas"] >= 5 for x in c)
        ver["V3"] = m("p1_p1ctl", "attain") >= s - 0.05
        ver["V4"] = m("p1_p1ctl", "p99_ms_first120") <= 0.8 * m("p1_safe", "p99_ms_first120")
    if all(len(arm(a)) >= 3 for a in ("p3_uncapped", "p3_cap10", "p3_gamma")):
        informative = m("p3_uncapped", "max_ejected") >= 4
        ver["G0_informative"] = informative
        if informative:
            ver["G1"] = m("p3_gamma", "goodput") >= m("p3_uncapped", "goodput") + 0.05
            ver["G2"] = m("p3_gamma", "goodput") >= m("p3_cap10", "goodput") - 0.02
            ver["G3"] = sum(x["faulty_ejected_end"] for x in arm("p3_gamma")) >= 2
    out["verdicts"] = {k: ("PASS" if v else "FAIL") if not isinstance(v, str) else v for k, v in ver.items()}
    print(json.dumps(out, indent=1)); json.dump(out, open("results_v4.json", "w"), indent=1)
if __name__ == "__main__": main()
