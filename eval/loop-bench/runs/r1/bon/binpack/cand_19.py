def priority(item, bins):
    """Maximise the share of free room the item takes, but shun slivers under a quarter of the item."""
    out = []
    sliver = 0.25 * item
    for b in bins[:-1]:
        r = b - item
        if r == 0:
            out.append(2.0)
        elif r < sliver:
            out.append(item / b - 0.5)
        else:
            out.append(item / b)
    out.append(-1.0)
    return out
