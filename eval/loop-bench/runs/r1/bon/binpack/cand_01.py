def priority(item, bins):
    """Best fit, but avoid leaving a sliver smaller than 8% of capacity."""
    cap = bins[-1]
    frag = cap * 0.08
    out = []
    for b in bins[:-1]:
        r = b - item
        if r == 0:
            out.append(float(cap))
        elif r < frag:
            out.append(-r - 1.5 * frag)
        else:
            out.append(-float(r))
    out.append(-10.0 * cap)
    return out
