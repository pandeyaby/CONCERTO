#!/usr/bin/env python3
"""Emit <monotonic_secs>,<replicas> every 5s. Monotonic clock avoids wall-clock suspend gaps."""
import subprocess, sys, time

ns, t0 = sys.argv[1], time.monotonic()
while True:
    try:
        r = subprocess.check_output(
            ["timeout", "8", "kubectl", "-n", ns, "get", "deploy", "app",
             "-o", "jsonpath={.status.replicas}"],
            stderr=subprocess.DEVNULL, text=True).strip()
        if r:
            print("%d,%s" % (int(time.monotonic() - t0), r), flush=True)
    except Exception:
        pass
    time.sleep(5)
