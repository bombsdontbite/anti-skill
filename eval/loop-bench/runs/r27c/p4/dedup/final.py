from collections import Counter
from itertools import chain


def near_duplicates(records):
    sets = list(map(frozenset, map(str.split, records)))
    empty = frozenset()
    d = dict(zip(sets, range(len(sets))))
    d.pop(empty, None)
    pairs = []
    # Records sharing a token set: every one of them, not just the last, goes into each pair.
    groups = {}
    if len(d) + sets.count(empty) < len(sets):
        last = list(map(d.get, sets))
        for i in [i for i, j in enumerate(last) if j is not None and j != i]:
            s = sets[i]
            g = groups.get(s)
            if g is None:
                groups[s] = [i]
            else:
                g.append(i)
        for s, g in groups.items():
            g.append(d[s])
            for a in range(len(g)):
                ga = g[a]
                for gb in g[a + 1:]:
                    pairs.append((ga, gb))

    def add(k, x, o, y):
        if groups and (k in groups or o in groups):
            for x2 in groups.get(k, (x,)):
                for y2 in groups.get(o, (y,)):
                    pairs.append((x2, y2) if x2 < y2 else (y2, x2))
        else:
            pairs.append((x, y) if x < y else (y, x))

    uniq = sorted(d, key=len)
    dk = d.keys()
    # Two distinct sets of at most 8 tokens match only when the smaller is the larger minus one
    # token, so up to 8 tokens the partners are found by lookup; below 5 the larger side finds them.
    j = 0
    for k in uniq:
        n = len(k)
        if n > 7:
            break
        j += 1
        if n > 4:
            for o in dk & map(k.difference, zip(k)):
                add(k, d[k], o, d[o])
    del uniq[:j]

    # From 8 tokens up, prefix filtering with the rarest tokens first.
    freq = Counter(chain.from_iterable(uniq))
    for r, t in enumerate(sorted(freq, key=freq.get)):
        freq[t] = r
    rg = freq.get
    ids = list(map(d.get, uniq))
    lens = list(map(len, uniq))
    index = {}
    ig = index.get
    gi = 0
    for k in uniq:
        n = lens[gi]
        x = ids[gi]
        if n == 8:
            for o in dk & map(k.difference, zip(k)):
                add(k, x, o, d[o])
            t = min(k, key=rg)
            lst = ig(t)
            if lst is None:
                index[t] = [gi]
            else:
                lst.append(gi)
            gi += 1
            continue
        minlen = (4 * n + 4) // 5
        toks = sorted(k, key=rg)
        cands = set()
        for t in toks[:n - minlen + 1]:
            lst = ig(t)
            if lst:
                cands.update(lst)
        lim = 4 * n
        for gj in cands:
            o = uniq[gj]
            m = lens[gj]
            if m >= minlen and 9 * len(k & o) >= lim + 4 * m:
                add(k, x, o, ids[gj])
        for t in toks[:n - (8 * n + 8) // 9 + 1]:
            lst = ig(t)
            if lst is None:
                index[t] = [gi]
            else:
                lst.append(gi)
        gi += 1
    return pairs
