"""Detuning sweep on the Prop 2 model: vary shedder gain gF and autoscaler
stabilization window W (masked signal, shedder trips at 60% util, HPA target 70%), compare against P2 at default tuning."""
from .prop2 import simulate

def run():
    rows = []
    for gF in (0.25, 1.0, 4.0):
        for W in (0.0, 60.0, 300.0, 900.0):
            r = simulate("masked", gF=gF, W=W, shed_util=0.6); rows.append(r)
    for tgt in (0.5, 0.55):  # retune HPA target below the shed threshold
        rows.append(simulate("masked", shed_util=0.6, target=tgt))
    rows.append(simulate("p2", shed_util=0.6))
    return rows
