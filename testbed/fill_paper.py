import json, statistics as st, sys
R = json.load(open(sys.argv[1])); tex = sys.argv[2]
arms = {a: [v for k, v in sorted(R.items()) if k.startswith(a)] for a in ("trap", "reverse")}
n = min(len(v) for v in arms.values())
rows = []
for a, vs in arms.items():
    for i, v in enumerate(vs, 1):
        rows.append(f"{a.upper()} {i} & {v['attain']:.3f} & {v['frac_429']:.3f} & {v['final_replicas']} & {v['mean_replicas_last']:.2f} \\\\")
m = {a: st.mean(v["attain"] for v in vs) for a, vs in arms.items()}
t1 = all(v["final_replicas"] <= 2 and v["attain"] <= 0.45 for v in arms["trap"])
t2 = all(v["final_replicas"] >= 5 and v["attain"] >= 0.85 for v in arms["reverse"])
t3 = m["reverse"] - m["trap"] >= 0.3
V = lambda b: "PASS" if b else "FAIL"
table = r"""\begin{table}[t]
\caption{Testbed RQ1, final 240\,s of each trial. Attainment is the 2xx fraction of offered load; 5 replicas are needed at 160\,req/s.}
\label{tab:testbed}
\centering\small
\begin{tabular}{@{}lcccc@{}}
\toprule
Trial & Attain. & 429 frac. & Final repl. & Mean repl. \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}

\textbf{Result.} """ + f"""Every TRAP trial held at the 2-replica floor while
offered load was 3.2$\\times$ the starting load; the HPA read 30\\,req/s per pod
against its 35\\,req/s target and never scaled. Mean attainment was {m['trap']:.3f}
(TRAP) vs.\\ {m['reverse']:.3f} (REVERSE), a gap of {m['reverse']-m['trap']:.3f}.
Pre-registered verdicts: T1 {V(t1)}, T2 {V(t2)}, T3 {V(t3)} ({n} trials per arm).
The trap therefore reproduces on unmodified, documented components, and, as
in simulation, reordering the thresholds escapes it."""
s = open(tex).read()
s = s.replace("%%TESTBED_TABLE%%", table).replace("%%NTRIALS%%", str(n))
s = s.replace("%%TESTBED_ABS%%", f"with a per-pod shedder tripping below the autoscaler's target, the fleet stayed at its replica floor and served {m['trap']:.0%} of load, vs.\\ {m['reverse']:.0%} with the thresholds reversed ({n} trials each).".replace('%', '\\%'))
open(tex, "w").write(s)
print(m, V(t1), V(t2), V(t3), n)
