#!/bin/bash
# Analyze completed trials (phase-2 480 s, gap <= 10 s), fill paper from template, build PDF.
cd $(dirname $0) && python3 - <<'PY'
import json, os
from analyze import analyze
r = {}
for k in sorted(os.listdir("runs")):
    try: a = analyze("runs/" + k)
    except Exception: continue
    if a["phase2_duration_s"] >= 470 and a["max_sample_gap_s"] <= 10: r[k] = a
json.dump(r, open("results.json", "w"), indent=1); print(json.dumps(r))
PY
cp ../paper/concerto.template.tex ../paper/concerto.tex && python3 fill_paper.py results.json ../paper/concerto.tex
cd ../paper && /tmp/tectonic -X compile concerto.tex 2>&1 | grep -iE "error|overfull"; pdfinfo concerto.pdf | grep Pages
