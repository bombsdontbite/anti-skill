_st = {"cap": None, "smin": None}


def priority(item, bins):
    """Best fit; a residual smaller than any item seen so far is dead space and is ranked last."""
    cap = bins[-1]
    if _st["cap"] != cap:
        _st["cap"] = cap
        _st["smin"] = item
    elif item < _st["smin"]:
        _st["smin"] = item
    smin = _st["smin"]
    out = []
    for b in bins[:-1]:
        r = b - item
        if r == 0:
            out.append(float(cap))
        elif r < smin:
            out.append(-r - float(cap))
        else:
            out.append(-float(r))
    out.append(-3.0 * cap)
    return out
