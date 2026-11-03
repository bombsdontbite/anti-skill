def priority(item, bins):
    """Large items go best fit; small items go first fit, so old bins get topped up."""
    cap = bins[-1]
    n = len(bins)
    if item * 3 > cap:
        return [-(b - item) for b in bins]
    out = []
    for i in range(n - 1):
        if bins[i] == item:
            out.append(float(n + 1))
        else:
            out.append(float(n - i))
    out.append(0.0)
    return out
