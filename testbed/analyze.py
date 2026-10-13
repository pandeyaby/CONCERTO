import subprocess, sys, json, csv, io, os


def analyze(d, last=240):
    v2 = f"{d}/v2.bin"
    if not os.path.exists(v2) or os.path.getsize(v2) == 0:
        raise FileNotFoundError(v2)
    out = subprocess.run(
        ["vegeta", "encode", "--to", "csv", v2], capture_output=True, text=True
    ).stdout
    rows = [(int(r[0]), int(r[1])) for r in csv.reader(io.StringIO(out)) if r]
    if not rows:
        raise ValueError(f"no vegeta rows in {v2}")
    t1 = max(t for t, _ in rows)
    win = [c for t, c in rows if t >= t1 - last * 1e9]
    if not win:
        win = [c for _, c in rows]
    rep_path = f"{d}/replicas.csv"
    rep = []
    if os.path.exists(rep_path):
        for l in open(rep_path):
            parts = l.strip().split(",")
            if len(parts) == 2 and parts[1].strip().isdigit():
                rep.append((int(parts[0]), int(parts[1])))
    gaps = [b[0] - a[0] for a, b in zip(rep, rep[1:])] if len(rep) > 1 else [0]
    sec = sorted(t // 10**9 for t, _ in rows)
    dur = sec[-1] - sec[0] if len(sec) > 1 else 0
    if rep:
        tr1 = rep[-1][0]
        rw = [r for t, r in rep if t >= tr1 - last] or [rep[-1][1]]
        final_r, max_r, mean_r = rep[-1][1], max(r for _, r in rep), round(sum(rw) / len(rw), 2)
    else:
        final_r = max_r = mean_r = None
    n = len(win)
    return {
        "max_sample_gap_s": max(gaps) if gaps else 0,
        "phase2_duration_s": dur,
        "attain": round(sum(c == 200 for c in win) / n, 4),
        "n": n,
        "frac_429": round(sum(c == 429 for c in win) / n, 4),
        "frac_503": round(sum(c == 503 for c in win) / n, 4),
        "final_replicas": final_r,
        "max_replicas": max_r,
        "mean_replicas_last": mean_r,
    }


def analyze_p3(d):
    """Full-window metrics for the 180 s P3 runs."""
    a = analyze(d, last=10**9)
    ejected = None
    clusters = f"{d}/clusters.txt"
    if os.path.exists(clusters):
        text = open(clusters).read()
        # Count hosts marked ejected / unhealthy if present
        ejected = text.count("failed_outlier_check") + text.count("/failed")
    a["ejected_hint"] = ejected
    return a


if __name__ == "__main__":
    res = {}
    for l in sorted(os.listdir("runs")):
        path = f"runs/{l}"
        if not os.path.isdir(path):
            continue
        try:
            res[l] = analyze_p3(path) if l.startswith("p3_") else analyze(path)
        except Exception as e:
            res[l] = {"error": str(e)}
    print(json.dumps(res, indent=1))
    json.dump(res, open("results_campaign.json", "w"), indent=1)
