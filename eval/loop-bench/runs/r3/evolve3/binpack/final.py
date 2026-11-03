# Sum-of-Squares (Csirik et al.) on a mirror of every open bin, which the caller only shows in part.
# A gap below the smallest item seen so far can never be used: it costs DEADW per unit instead of a count.
DEADW = 1.0
_S = {'cap': None, 'gaps': [], 'N': None, 'mn': 10 ** 9}


def _reset(cap, gaps):
    # New instance, or the mirror no longer matches what the caller shows: rebuild from what is visible.
    _S['cap'] = cap
    _S['gaps'] = list(gaps)
    N = _S['N'] = [0] * (cap + 1)
    for g in gaps:
        N[g] += 1
    if not gaps:
        _S['mn'] = 10 ** 9


def _commit(item, bins, j):
    gaps = _S['gaps']; N = _S['N']; cap = _S['cap']
    if j == len(bins) - 1:
        gaps.append(cap - item); N[cap - item] += 1
        return
    k = -1
    for i in range(len(gaps)):
        if gaps[i] >= item:
            k += 1
            if k == j:
                break
    g = gaps[i]; N[g] -= 1; gaps[i] = g - item; N[g - item] += 1


def priority(item, bins):
    cap = bins[-1]
    if _S['cap'] != cap or [g for g in _S['gaps'] if g >= item] != bins[:-1]:
        _reset(cap, bins[:-1])
    if item < _S['mn']:
        _S['mn'] = item
    N = _S['N']; mn = _S['mn']

    def add(r):
        if r <= 0:
            return 0.0
        if r < mn:
            return DEADW * r
        return 2 * N[r] + 1

    def rem(g):
        if g < mn:
            return -DEADW * g
        return 1 - 2 * N[g]

    out = []
    for g in bins[:-1]:
        r = g - item
        out.append(-(add(r) + rem(g)) - 1e-6 * r)
    r = cap - item
    out.append(-add(r) - 1e-6 * r)
    j = 0
    for k in range(1, len(out)):
        if out[k] > out[j]:
            j = k
    _commit(item, bins, j)
    return out
