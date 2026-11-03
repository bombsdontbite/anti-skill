_st = {"cap": None, "mu": None}


def priority(item, bins):
    """Near-perfect fits first; otherwise leave a gap about the size of an average item."""
    cap = bins[-1]
    if _st["cap"] != cap or _st["mu"] is None:
        _st["cap"] = cap
        _st["mu"] = float(item)
    else:
        _st["mu"] += (item - _st["mu"]) * 0.01
    mu = _st["mu"]
    tol = 0.02 * cap
    out = []
    for b in bins[:-1]:
        r = b - item
        if r <= tol:
            out.append(10.0 * cap - r)
        else:
            out.append(-abs(r - mu) - 0.1 * r)
    out.append(-10.0 * cap)
    return out
