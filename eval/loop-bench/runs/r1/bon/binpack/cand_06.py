def priority(item, bins):
    """Prefer bins whose leftover would be filled best by more items of this same size."""
    out = []
    for b in bins[:-1]:
        r = b - item
        if r == 0:
            out.append(1e12)
            continue
        left = r % item
        out.append(-float(left) - 0.05 * r)
    out.append(-1e12)
    return out
