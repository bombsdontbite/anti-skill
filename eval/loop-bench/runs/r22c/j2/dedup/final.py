from collections import Counter
from itertools import chain


def near_duplicates(records):
    groups = {}
    gget = groups.get
    for i, s in enumerate(map(frozenset, map(str.split, records))):
        g = gget(s)
        if g is None:
            groups[s] = [i]
        else:
            g.append(i)
    groups.pop(frozenset(), None)
    pairs = []
    app = pairs.append
    for gi in groups.values():
        if len(gi) > 1:
            for x in range(len(gi)):
                for y in range(x + 1, len(gi)):
                    app((gi[x], gi[y]))
    # sets of up to 3 tokens are near-duplicates only of identical sets
    keys = [s for s in groups if len(s) > 3]
    if not keys:
        return pairs
    keys.sort(key=len)
    freq = Counter(chain.from_iterable(keys))
    rank = {t: k for k, t in enumerate(sorted(freq, key=freq.get))}
    rget = rank.get
    index = {}
    iget = index.get
    for s in keys:
        n = len(s)
        minb = (4 * n + 4) // 5
        toks = sorted(s, key=rget)
        # probe with the prefix for partners as short as minb, index the
        # shorter prefix that suffices for partners at least as long as s
        ip = n - (8 * n + 8) // 9 + 1
        cands = None
        for t in toks[:n - minb + 1]:
            lst = iget(t)
            if lst:
                if len(lst[0]) < minb:
                    k = 1
                    while k < len(lst) and len(lst[k]) < minb:
                        k += 1
                    del lst[:k]
                if cands is None:
                    cands = set(lst)
                else:
                    cands.update(lst)
        for t in toks[:ip]:
            lst = iget(t)
            if lst is None:
                index[t] = [s]
            else:
                lst.append(s)
        if cands:
            gi = groups[s]
            for c in cands:
                if 9 * len(s & c) >= 4 * (n + len(c)):
                    for a in groups[c]:
                        for b in gi:
                            app((a, b) if a < b else (b, a))
    return pairs
