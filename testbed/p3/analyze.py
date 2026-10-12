import subprocess, csv, io, json, os
def analyze(d, last=180):
    out = subprocess.run(["vegeta", "encode", "--to", "csv", f"{d}/v.bin"], capture_output=True, text=True).stdout
    rows = [(int(r[0]), int(r[1])) for r in csv.reader(io.StringIO(out))]
    s = sorted(t // 10**9 for t, _ in rows); t1 = max(t for t, _ in rows)
    win = [c for t, c in rows if t >= t1 - last * 1e9]
    ej = [tuple(map(int, l.strip().split(","))) for l in open(f"{d}/ejected.csv") if l.strip().count(",") == 1 and l.strip().split(",")[1]]
    gaps = [b[0] - a[0] for a, b in zip(ej, ej[1:])] or [0]
    faulty = open(f"{d}/faulty.txt").read().strip()
    endc = open(f"{d}/clusters_end.txt").read()
    return {"goodput": round(sum(c == 200 for c in win) / len(win), 4), "n": len(win), "duration_s": s[-1] - s[0],
            "max_gap_s": max(gaps), "max_ejected": max(e for _, e in ej), "mean_ejected_last": round(sum(e for t, e in ej if t >= ej[-1][0] - last) / max(1, sum(1 for t, e in ej if t >= ej[-1][0] - last)), 2),
            "faulty_ejected_at_end": f"app::{faulty}:9000::health_flags::/failed_outlier_check" in endc}
if __name__ == "__main__":
    r = {k: analyze("runs/" + k) for k in sorted(os.listdir("runs")) if os.path.exists(f"runs/{k}/clusters_end.txt")}
    print(json.dumps(r, indent=1)); json.dump(r, open("results.json", "w"), indent=1)
