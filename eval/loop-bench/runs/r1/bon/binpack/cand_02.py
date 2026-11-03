def priority(item, bins):
    """Weibull-style polynomial score with a neighbour-difference step."""
    m = max(bins)
    i2 = float(item) * item
    i3 = i2 * item
    raw = []
    for b in bins:
        s = (b - m) ** 2 / item + b * b / i2 + b * b / i3
        if b > item:
            s = -s
        raw.append(s)
    out = [raw[0]]
    for k in range(1, len(raw)):
        out.append(raw[k] - raw[k - 1])
    return out
