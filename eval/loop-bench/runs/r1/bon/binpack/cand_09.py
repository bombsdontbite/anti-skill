def priority(item, bins):
    """Best fit blended with a mild pull towards older bins."""
    cap = bins[-1]
    n = len(bins) - 1
    if n == 0:
        return [0.0]
    w = 0.03 * cap / n
    out = []
    for i in range(n):
        r = bins[i] - item
        if r == 0:
            out.append(float(cap))
        else:
            out.append(-r - w * i)
    out.append(-3.0 * cap)
    return out
