def priority(item, bins):
    """Coarse best fit: leftovers within the same 2%-of-capacity band tie, and the oldest bin wins."""
    cap = bins[-1]
    band = max(1.0, cap * 0.02)
    out = []
    for b in bins[:-1]:
        r = b - item
        if r == 0:
            out.append(1.0)
        else:
            out.append(-float(int(r // band)) - 0.5)
    out.append(-float(cap) * 10)
    return out
