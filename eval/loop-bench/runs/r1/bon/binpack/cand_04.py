def priority(item, bins):
    """Quadratic penalty on spare room, with the tightest bin rescaled by item size."""
    score = [1000.0 - b * (b - item) for b in bins]
    idx = 0
    for k in range(1, len(bins)):
        if bins[k] < bins[idx]:
            idx = k
    score[idx] = score[idx] * item - (bins[idx] - item) ** 4
    return score
