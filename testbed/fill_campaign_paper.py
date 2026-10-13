#!/usr/bin/env python3
"""Insert PREREG v3 campaign results into paper/concerto.tex placeholders."""
from __future__ import annotations

import json
import statistics as st
import sys

results = json.load(open(sys.argv[1]))
verdicts = json.load(open(sys.argv[2]))
tex_path = sys.argv[3]


def arm(prefix):
    return [v for k, v in sorted(results.items()) if k.startswith(prefix) and "error" not in v]


def mean(xs, key):
    return st.mean(v[key] for v in xs) if xs else float("nan")


def rows(prefix, name):
    out = []
    for i, v in enumerate(arm(prefix), 1):
        rej = v.get("frac_503", 0) + v.get("frac_429", 0)
        out.append(
            f"{name} {i} & {v['attain']:.3f} & {rej:.3f} & {v['final_replicas']} & {v['mean_replicas_last']:.2f} \\\\"
        )
    return out


ac_rows = rows("ac_trap_", "AC-TRAP") + rows("ac_reverse_", "AC-REV")
tt_rows = rows("tt_safe_", "TT-SAFE") + rows("tt_indep_", "TT-INDEP") + rows("p1_budget_", "P1")
p3_rows = []
for pref, name in [
    ("p3_none_", "none"),
    ("p3_maxej10_", "maxej10"),
    ("p3_minhealth50_", "minhealth50"),
    ("p3_gamma_", "gamma"),
]:
    for i, v in enumerate(arm(pref), 1):
        p3_rows.append(f"{name} {i} & {v['attain']:.3f} & {v.get('frac_503', 0):.3f} & {v['final_replicas']} \\\\")

v = verdicts
section = r"""
\section{Testbed Campaign: AC, Two-Tier, P1, P3}
\label{sec:campaign}

Thresholds were committed in \texttt{PREREG.md} v3 before any of these runs.
The stack matches Section~\ref{sec:testbed} unless noted.

\subsection{E-AC: adaptive-concurrency trap}

Pinned Envoy \texttt{adaptive\_concurrency} ($L{=}2$ TRAP, $L{=}6$ REVERSE) on the
503 rejection path. Verdicts: AC1 """ + v.get("AC1", "?") + ", AC2 " + v.get("AC2", "?") + ", AC3 " + v.get("AC3", "?") + r""".

\begin{table}[t]
\caption{E-AC final 240\,s. Reject frac.\ counts 503s.}
\label{tab:ac}
\centering\small
\begin{tabular}{@{}lcccc@{}}
\toprule
Trial & Attain. & Reject & Final repl. & Mean repl. \\
\midrule
""" + "\n".join(ac_rows) + r"""
\bottomrule
\end{tabular}
\end{table}

\subsection{E-two-tier and E-P1}

Independent edge+sidecar \texttt{local\_ratelimit} vs.\ a shared refill budget.
Verdicts: TT1 """ + v.get("TT1", "?") + ", TT2 " + v.get("TT2", "?") + ", TT3 " + v.get("TT3", "?") + "; P1a " + v.get("P1a", "?") + ", P1b " + v.get("P1b", "?") + ", P1c " + v.get("P1c", "?") + r""".

\begin{table}[t]
\caption{Two-tier and P1, final 240\,s. Reject frac.\ counts 429s.}
\label{tab:twotier}
\centering\small
\begin{tabular}{@{}lcccc@{}}
\toprule
Trial & Attain. & Reject & Final repl. & Mean repl. \\
\midrule
""" + "\n".join(tt_rows) + r"""
\bottomrule
\end{tabular}
\end{table}

\subsection{E-P3: outlier caps}

Fixed 10-endpoint pool (9 healthy + 1 always-503), 200\,req/s for 180\,s, HPA off.
Verdicts: P3a """ + v.get("P3a", "?") + ", P3b " + v.get("P3b", "?") + ", P3c " + v.get("P3c", "?") + r""".

\begin{table}[t]
\caption{E-P3 full-window goodput (2xx fraction).}
\label{tab:p3}
\centering\small
\begin{tabular}{@{}lccc@{}}
\toprule
Trial & Goodput & 503 frac. & Endpoints \\
\midrule
""" + "\n".join(p3_rows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""

# Soften the "future work" and AC caveat lines when campaign data exists.
s = open(tex_path).read()
if "%%CAMPAIGN_SECTION%%" in s:
    s = s.replace("%%CAMPAIGN_SECTION%%", section)
else:
    # Insert before Related Work if placeholder missing
    needle = "\\section{Related Work}"
    if needle in s and "\\label{sec:campaign}" not in s:
        s = s.replace(needle, section + "\n" + needle)
s = s.replace(
    "Further testbed experiments (P1, P3, and the arbiter itself) are future work.",
    "A follow-on testbed campaign (Section~\\ref{sec:campaign}) exercises adaptive concurrency, two-tier shedding, a P1 budget stand-in, and outlier caps; the arbiter itself remains future work.",
)
s = s.replace(
    "shedder; Envoy's adaptive concurrency was not tested.",
    "shedder. Section~\\ref{sec:campaign} retests the trap with Envoy adaptive concurrency.",
)
open(tex_path, "w").write(s)
print("filled", tex_path)
print(json.dumps({k: verdicts[k] for k in verdicts if k.startswith(("AC", "TT", "P1", "P3"))}, indent=2))
