from collections import Counter
from itertools import chain


def near_duplicates(records):
    groups = {}
    i = 0
    for s in map(frozenset, map(str.split, records)):
        if s:
            g = groups.get(s)
            if g is None:
                groups[s] = [i]
            else:
                g.append(i)
        i += 1
    pairs = []
    for g in groups.values():
        if len(g) > 1:
            for a in range(len(g)):
                ga = g[a]
                for b in g[a + 1:]:
                    pairs.append((ga, b))
    # Distinct sets of up to 3 tokens never reach 0.8; size 4 only meets size-5 supersets.
    sets = sorted([s for s in groups if len(s) > 3], key=len)
    freq = Counter(chain.from_iterable(sets))
    w = len(freq)
    rank = {t: c * w + k for k, (t, c) in enumerate(freq.items())}
    rk = rank.__getitem__
    index = {}
    get = index.get
    for x, a in enumerate(sets):
        n = len(a)
        if n == 4:
            t = min(a, key=rk)
            lst = get(t)
            if lst is None:
                index[t] = [x]
            else:
                lst.append(x)
            continue
        toks = sorted(a, key=rk)
        cands = set()
        for t in toks[:n - (4 * n + 4) // 5 + 1]:
            lst = get(t)
            if lst:
                cands.update(lst)
        if cands:
            ga = groups[a]
            minlen4 = 4 * n
            for y in cands:
                b = sets[y]
                lb = len(b)
                if 5 * lb >= minlen4:
                    inter = len(a & b)
                    if 5 * inter >= 4 * (n + lb - inter):
                        gb = groups[b]
                        for i in ga:
                            for j in gb:
                                pairs.append((i, j) if i < j else (j, i))
        for t in toks[:n - (8 * n + 8) // 9 + 1]:
            lst = get(t)
            if lst is None:
                index[t] = [x]
            else:
                lst.append(x)
    return pairs
