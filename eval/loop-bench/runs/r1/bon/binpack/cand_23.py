def priority(item, bins):
    """Three tiers: exact fit; best fit among bins that end at least 90% full; else first fit."""
    cap = bins[-1]
    n = len(bins) - 1
    out = []
    for i in range(n):
        r = bins[i] - item
        if r == 0:
            out.append(3.0)
        elif r <= 0.1 * cap:
            out.append(2.0 - r / cap)
        else:
            out.append(1.0 - i / (n + 1.0))
    out.append(0.0)
    return out
