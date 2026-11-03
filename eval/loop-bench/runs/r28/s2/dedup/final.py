from collections import Counter
from itertools import chain


def near_duplicates(records):
    fs = list(map(frozenset, map(str.split, records)))
    last = dict(zip(fs, range(len(fs))))
    last.pop(frozenset(), None)
    pairs = []
    extra = {}
    if len(last) < len(fs):
        for i, s in enumerate(fs):
            j = last.get(s)
            if j is not None and j != i:
                g = extra.get(s)
                if g is None:
                    extra[s] = [i]
                else:
                    g.append(i)
        for s, g in extra.items():
            g.append(last[s])
            for x, gx in enumerate(g):
                for y in g[x + 1:]:
                    pairs.append((gx, y))
    sets = sorted(last, key=len)
    freq = Counter(chain.from_iterable(sets))
    rank = {t: i for i, t in enumerate(sorted(freq, key=freq.__getitem__))}
    key = rank.__getitem__
    index = {}
    lens = []
    get = index.get
    for k, a in enumerate(sets):
        n = len(a)
        lens.append(n)
        minlen = (4 * n + 4) // 5
        if minlen == n:
            t = min(a, key=key)
            lst = get(t)
            if lst is None:
                index[t] = [k]
            else:
                lst.append(k)
            continue
        toks = sorted(a, key=key)
        q = n - (8 * n + 8) // 9 + 1
        cands = set()
        for t in toks[:q]:
            lst = get(t)
            if lst is None:
                index[t] = [k]
            else:
                cands.update(lst)
                lst.append(k)
        for t in toks[q:n - minlen + 1]:
            lst = get(t)
            if lst is not None:
                cands.update(lst)
        for m in cands:
            lm = lens[m]
            if lm >= minlen:
                b = sets[m]
                if 9 * len(a & b) >= 4 * (n + lm):
                    ga = extra.get(a)
                    gb = extra.get(b)
                    if ga is None and gb is None:
                        i = last[a]; j = last[b]
                        pairs.append((i, j) if i < j else (j, i))
                    else:
                        for j in gb or (last[b],):
                            for i in ga or (last[a],):
                                pairs.append((i, j) if i < j else (j, i))
    return pairs
