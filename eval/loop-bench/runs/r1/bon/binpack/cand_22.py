from bisect import bisect_left, bisect_right


def priority(item, bins):
    """Best fit that avoids crowding many bins at the same gap, keeping a spread of hole sizes."""
    cap = bins[-1]
    open_ = sorted(bins[:-1])
    tol = 0.01 * cap
    w = 0.03 * cap
    out = []
    for b in bins[:-1]:
        r = b - item
        if r == 0:
            out.append(float(cap))
            continue
        crowd = bisect_right(open_, r + tol) - bisect_left(open_, r - tol)
        out.append(-r - w * crowd)
    out.append(-float(cap) * 10)
    return out
