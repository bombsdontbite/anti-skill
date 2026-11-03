_st = {"cap": None, "mean": None}


def priority(item, bins):
    """Prefer leftovers close to a whole number of average-sized items, then the tightest."""
    cap = bins[-1]
    if _st["cap"] != cap or _st["mean"] is None:
        _st["cap"] = cap
        _st["mean"] = float(item)
    else:
        _st["mean"] += (item - _st["mean"]) * 0.02
    mu = max(1.0, _st["mean"])
    out = []
    for b in bins[:-1]:
        r = b - item
        if r == 0:
            out.append(float(cap))
            continue
        m = r % mu
        d = min(m, mu - m) if r >= mu else r
        out.append(-0.3 * r - d)
    out.append(-5.0 * cap)
    return out
