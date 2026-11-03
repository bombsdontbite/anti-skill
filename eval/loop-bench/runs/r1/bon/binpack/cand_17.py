def priority(item, bins):
    """Tiny items go to the roomiest open bin (keeping tight gaps for mid sizes); the rest go best fit."""
    cap = bins[-1]
    if len(bins) == 1:
        return [0.0]
    tiny = item * 10 <= cap
    out = []
    for b in bins[:-1]:
        r = b - item
        if r == 0:
            out.append(float(cap) * 2)
        elif tiny:
            out.append(float(r))
        else:
            out.append(-float(r))
    out.append(-float(cap) * 3)
    return out
