import math
def ci(xs):
    n = len(xs); m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1)) if n > 1 else 0.0
    h = 1.96 * sd / math.sqrt(n)
    return {"mean": round(m, 4), "lo": round(m - h, 4), "hi": round(m + h, 4), "n": n}
def diff_ci(a, b):
    return ci([x - y for x, y in zip(a, b)])  # paired by seed
