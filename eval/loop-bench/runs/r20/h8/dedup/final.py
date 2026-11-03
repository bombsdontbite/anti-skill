from collections import Counter
from itertools import chain


def near_duplicates(records):
    n_rec = len(records)
    fs = list(map(frozenset, map(str.split, records)))
    last = dict(zip(fs, range(n_rec)))
    last.pop(frozenset(), None)
    pairs = []
    multi = {}
    lget = last.get
    for i in [i for i, j in enumerate(map(lget, fs)) if i != j]:
        s = fs[i]
        if s:
            g = multi.get(s)
            if g is None:
                multi[s] = [i]
            else:
                g.append(i)
    for s, g in multi.items():
        g.append(last[s])
        for x in range(len(g)):
            gx = g[x]
            for y in range(x + 1, len(g)):
                pairs.append((gx, g[y]))
    # Sets of three or fewer tokens can only match an identical set.
    sets = sorted([s for s in last if len(s) > 3], key=len)
    if len(sets) < 2:
        return pairs
    freq = Counter(chain.from_iterable(sets))
    order = sorted(freq, key=freq.__getitem__)
    rget = dict(zip(order, range(len(order)))).__getitem__
    lens = [len(s) for s in sets]
    idx = {}
    iget = idx.get
    mget = multi.get
    for k, s in enumerate(sets):
        n = lens[k]
        if n == 4:
            # Only an index entry: its rarest token, position 0.
            t = min(s, key=rget)
            lst = iget(t)
            if lst is None:
                idx[t] = [(k, 0)]
            else:
                lst.append((k, 0))
            continue
        toks = sorted(s, key=rget)
        minlen = (4 * n + 4) // 5
        cand = {}
        cget = cand.get
        for p in range(n - minlen + 1):
            lst = iget(toks[p])
            if lst:
                if lens[lst[0][0]] < minlen:
                    # Lists grow in length order and minlen never falls: drop the short head.
                    cut = 1
                    while cut < len(lst) and lens[lst[cut][0]] < minlen:
                        cut += 1
                    del lst[:cut]
                rest = n - p
                for m, q in lst:
                    lm = lens[m]
                    c = cget(m, 0)
                    if c < 0:
                        continue
                    r = lm - q
                    if c + (rest if rest < r else r) >= (4 * (n + lm) + 8) // 9:
                        cand[m] = c + 1
                    else:
                        cand[m] = -1
        if cand:
            ga = None
            for m, c in cand.items():
                if c > 0:
                    b = sets[m]
                    inter = len(s & b)
                    if 5 * inter >= 4 * (n + lens[m] - inter):
                        if ga is None:
                            ga = mget(s) or [last[s]]
                        for j in mget(b) or (last[b],):
                            for i in ga:
                                pairs.append((i, j) if i < j else (j, i))
        for p in range(n - (8 * n + 8) // 9 + 1):
            t = toks[p]
            lst = iget(t)
            if lst is None:
                idx[t] = [(k, p)]
            else:
                lst.append((k, p))
    return pairs
