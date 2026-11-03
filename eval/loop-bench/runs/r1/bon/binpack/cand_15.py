def priority(item, bins):
    """Best fit, nudged towards bins whose current load looks like a multiple of this item's size."""
    cap = bins[-1]
    out = []
    for b in bins[:-1]:
        r = b - item
        if r == 0:
            out.append(float(cap))
            continue
        load = cap - b
        m = load % item
        d = min(m, item - m)
        out.append(-r - 0.5 * d)
    out.append(-5.0 * cap)
    return out
