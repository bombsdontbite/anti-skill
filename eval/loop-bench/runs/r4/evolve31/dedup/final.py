from collections import Counter
from itertools import chain


def near_duplicates(records):
    groups = {}
    for i, r in enumerate(records):
        s = frozenset(r.split())
        g = groups.get(s)
        if g is None:
            groups[s] = [i]
        else:
            g.append(i)
    groups.pop(frozenset(), None)
    pairs = []
    for g in groups.values():
        if len(g) > 1:
            for a in range(len(g)):
                ga = g[a]
                for b in g[a + 1:]:
                    pairs.append((ga, b))
    # Distinct sets of up to 3 tokens can only match an identical set.
    keys = [s for s in groups if len(s) > 3]
    if not keys:
        return pairs
    freq = Counter(chain.from_iterable(keys))
    rank = {t: k for k, t in enumerate(sorted(freq, key=freq.get))}
    rget = rank.get
    keys.sort(key=len)
    index = [[] for _ in range(len(rank))]
    L = [len(s) for s in keys]
    for x in range(len(keys)):
        xs = keys[x]
        lx = L[x]
        minlen = (4 * lx + 4) // 5
        tx = sorted(map(rget, xs))[: lx - minlen + 1]
        cand = set()
        for t in tx:
            cand.update(index[t])
        if cand:
            gx = None
            for y in cand:
                ly = L[y]
                if ly >= minlen and 9 * len(xs & keys[y]) >= 4 * (lx + ly):
                    if gx is None:
                        gx = groups[xs]
                    for a in gx:
                        for b in groups[keys[y]]:
                            pairs.append((a, b) if a < b else (b, a))
        for t in tx[: lx - (8 * lx + 8) // 9 + 1]:
            index[t].append(x)
    return pairs
