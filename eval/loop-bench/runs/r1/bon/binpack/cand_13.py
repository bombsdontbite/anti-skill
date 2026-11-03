import math


def priority(item, bins):
    """Best fit with a smooth Gaussian penalty around tiny, hard-to-use leftovers."""
    cap = float(bins[-1])
    a = 0.15 * cap
    c = 0.04 * cap
    w = 0.03 * cap
    out = []
    for b in bins[:-1]:
        r = b - item
        if r == 0:
            out.append(cap)
            continue
        z = (r - c) / w
        out.append(-r - a * math.exp(-z * z))
    out.append(-5.0 * cap)
    return out
