#!/usr/bin/env python3
"""Emit <monotonic_secs>,<ejected_count> every 5s. Monotonic clock avoids wall-clock suspend gaps."""
import subprocess, time

t0 = time.monotonic()
while True:
    try:
        out = subprocess.check_output(
            ["curl", "-s", "-m2", "http://127.0.0.1:30903/clusters"],
            stderr=subprocess.DEVNULL, text=True)
        n = out.count("failed_outlier_check")
        print("%d,%d" % (int(time.monotonic() - t0), n), flush=True)
    except Exception:
        pass
    time.sleep(5)
