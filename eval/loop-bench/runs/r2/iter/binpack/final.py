"""Sum-of-squares bin choice over a reconstructed gap profile.

priority() keeps a count of open bins per remaining-capacity value (the gap
profile), rebuilt from the bins it is shown and from its own past choices.
A placement is scored by how much it raises sum(N[g]^2) over live gaps; a gap
smaller than almost every item seen so far is dead and costs its size instead.
An exact fit always wins.
"""

DEAD_W = 1.0   # cost per unit of capacity left in a dead gap, in SS units
QUANT = 0.01   # gaps below this item-size quantile count as dead

_S = {'cap': 0}


def _reset(cap):
    _S['cap'] = cap
    _S['N'] = {}
    _S['H'] = {}
    _S['n'] = 0
    _S['mn'] = cap + 1
    _S['q'] = 0


def _sync(item, bins, cap):
    # Make the gap profile agree with the bins we were shown; a mismatch means
    # a new instance (or lost track), so start over from what is visible.
    N = _S['N']
    vis = {}
    for b in bins[:-1]:
        vis[b] = vis.get(b, 0) + 1
    ok = True
    for g, c in N.items():
        if g >= item and vis.get(g, 0) != c:
            ok = False
            break
    if ok:
        for g, c in vis.items():
            if N.get(g, 0) != c:
                ok = False
                break
    if not ok:
        if len(bins) == 1:
            _reset(cap)
        else:
            for g in [g for g in N if g >= item]:
                del N[g]
        _S['N'].update(vis)


def priority(item, bins):
    cap = bins[-1]
    if _S['cap'] != cap:
        _reset(cap)
    _sync(item, bins, cap)
    N = _S['N']
    H = _S['H']
    H[item] = H.get(item, 0) + 1
    _S['n'] += 1
    if item < _S['mn']:
        _S['mn'] = item
    if _S['n'] % 32 == 0:
        k = QUANT * _S['n']
        acc = 0
        for s in sorted(H):
            acc += H[s]
            if acc > k:
                _S['q'] = s
                break
    mn = max(_S['mn'], _S['q'])
    dw = DEAD_W

    def cost(g, c):
        if g <= 0 or c <= 0:
            return 0.0
        if g < mn:
            return dw * g * c
        return float(c * c)

    pr = []
    for b in bins:
        g = b - item
        if g == 0:
            pr.append(1e9)
            continue
        d = 0.0
        if b != cap:
            nb = N.get(b, 0)
            d += cost(b, nb - 1) - cost(b, nb)
        ng = N.get(g, 0)
        d += cost(g, ng + 1) - cost(g, ng)
        pr.append(-d - 1e-6 * g)

    j = 0
    for k in range(1, len(pr)):
        if pr[k] > pr[j]:
            j = k
    b = bins[j]
    g = b - item
    if b != cap:
        N[b] -= 1
        if N[b] == 0:
            del N[b]
    if g > 0:
        N[g] = N.get(g, 0) + 1
    return pr
