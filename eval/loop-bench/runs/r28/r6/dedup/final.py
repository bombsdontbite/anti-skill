from collections import Counter
from itertools import chain, combinations


def near_duplicates(records):
    allsets = list(map(frozenset, map(str.split, records)))
    groups = {}
    for i, s in enumerate(allsets):
        g = groups.get(s)
        if g is None:
            groups[s] = [i]
        else:
            g.append(i)
    groups.pop(frozenset(), None)
    pairs = []
    for g in groups.values():
        if len(g) > 1:
            pairs.extend(combinations(g, 2))
    sets = sorted(groups, key=len)
    if not sets:
        return pairs
    freq = Counter(chain.from_iterable(sets))
    rank = {t: r for r, t in enumerate(sorted(freq, key=lambda t: (freq[t], t)))}
    key = rank.__getitem__
    top = len(sets[-1]) + 1
    minl = [(4 * n + 4) // 5 for n in range(top)]
    plen = [n - minl[n] + 1 for n in range(top)]
    ilen = [n - (8 * n + 8) // 9 + 1 for n in range(top)]
    lens = list(map(len, sets))
    pres = [sorted(s, key=key)[:plen[n]] for s, n in zip(sets, lens)]
    gs = [groups[s] for s in sets]
    index = {}
    get = index.get
    for k in range(len(sets)):
        n = lens[k]
        need = minl[n]
        il = ilen[n]
        cand = None
        toks = pres[k]
        for t in toks[:il]:
            lst = get(t)
            if lst is None:
                index[t] = [1, k]
            else:
                p = lst[0]
                m = len(lst)
                if p < m and lens[lst[p]] < need:
                    p += 1
                    while p < m and lens[lst[p]] < need:
                        p += 1
                    lst[0] = p
                if cand is None:
                    cand = set(lst[p:])
                else:
                    cand.update(lst[p:])
                lst.append(k)
        for t in toks[il:]:
            lst = get(t)
            if lst is not None:
                p = lst[0]
                m = len(lst)
                if p < m and lens[lst[p]] < need:
                    p += 1
                    while p < m and lens[lst[p]] < need:
                        p += 1
                    lst[0] = p
                if cand is None:
                    cand = set(lst[p:])
                else:
                    cand.update(lst[p:])
        if cand:
            s = sets[k]
            gi = gs[k]
            lim = 4 * n
            for c in cand:
                if 9 * len(s & sets[c]) >= lim + 4 * lens[c]:
                    gj = gs[c]
                    if len(gi) == 1 and len(gj) == 1:
                        i = gi[0]; j = gj[0]
                        pairs.append((i, j) if i < j else (j, i))
                    else:
                        for i in gi:
                            for j in gj:
                                pairs.append((i, j) if i < j else (j, i))
    return pairs
