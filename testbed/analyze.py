import subprocess, sys, json, csv, io, os
def analyze(d, last=240):
    out = subprocess.run(["vegeta","encode","--to","csv",f"{d}/v2.bin"],capture_output=True,text=True).stdout
    rows = [(int(r[0]), int(r[1])) for r in csv.reader(io.StringIO(out))]
    t1 = max(t for t,_ in rows); win = [c for t,c in rows if t >= t1 - last*1e9]
    rep = [(int(a), int(b)) for a,b in (l.strip().split(",") for l in open(f"{d}/replicas.csv") if l.strip().split(",")[1])]
    tr1 = rep[-1][0]; rw = [r for t,r in rep if t >= tr1 - last]
    # freeze check: largest gap between consecutive replica samples (sampled every 5 s)
    gaps = [b[0]-a[0] for a,b in zip(rep, rep[1:])]
    sec = sorted(t//10**9 for t,_ in rows); dur = sec[-1]-sec[0]
    return {"max_sample_gap_s": max(gaps), "phase2_duration_s": dur, "attain": round(sum(c==200 for c in win)/len(win),4), "n": len(win),
            "frac_429": round(sum(c==429 for c in win)/len(win),4),
            "final_replicas": rep[-1][1], "max_replicas": max(r for _,r in rep), "mean_replicas_last": round(sum(rw)/len(rw),2)}
if __name__ == "__main__":
    res = {l: analyze(f"runs/{l}") for l in sorted(os.listdir("runs"))}
    print(json.dumps(res, indent=1)); json.dump(res, open("results.json","w"), indent=1)
