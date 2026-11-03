from collections import Counter
from itertools import chain


def near_duplicates(records):
    groups = {}
    for i, s in enumerate(map(frozenset, map(str.split, records))):
        g = groups.get(s)
        if g is None:
            groups[s] = [i]
        else:
            g.append(i)
    groups.pop(frozenset(), None)
    pairs = []
    for g in groups.values():
        k = len(g)
        if k > 1:
            for x in range(k):
                gx = g[x]
                for y in range(x + 1, k):
                    pairs.append((gx, g[y]))
    # Distinct sets of 3 or fewer tokens can never reach 80 %.
    big = [s for s in groups if len(s) > 3]
    if len(big) < 2:
        return pairs
    freq = Counter(chain.from_iterable(big))
    rank = {t: r for r, t in enumerate(sorted(freq, key=freq.get))}
    key = rank.get
    index = {}
    get = index.get
    for s in sorted(big, key=len):
        L = len(s)
        minl = (4 * L + 4) // 5
        # Probe: partners are no longer than s; index: partners are no shorter.
        pp = L - (4 * (L + minl) + 8) // 9 + 1
        pi = L - (8 * L + 8) // 9 + 1
        toks = sorted(s, key=key)
        cands = None
        for t in toks[:pi]:
            lst = get(t)
            if lst is None:
                index[t] = [s]
            else:
                if cands is None:
                    cands = set(lst)
                else:
                    cands.update(lst)
                lst.append(s)
        for t in toks[pi:pp]:
            lst = get(t)
            if lst is not None:
                if cands is None:
                    cands = set(lst)
                else:
                    cands.update(lst)
        if cands:
            gu = groups[s]
            for b in cands:
                lv = len(b)
                if lv >= minl and 9 * len(s & b) >= 4 * (L + lv):
                    for a in gu:
                        for c in groups[b]:
                            pairs.append((a, c) if a < c else (c, a))
    return pairs
