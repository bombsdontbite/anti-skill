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
            for x in range(len(g)):
                gx = g[x]
                for y in g[x + 1:]:
                    pairs.append((gx, y))
    sums = {sum(map(hash, s)) for s in groups if 3 < len(s) < 8}
    for s in groups:
        a = len(s)
        if 4 < a < 9:
            hs = list(map(hash, s))
            total = sum(hs)
            if sums.isdisjoint([total - h for h in hs]):
                continue
            for t in s:
                g = groups.get(s - {t})
                if g is not None:
                    for u in groups[s]:
                        for v in g:
                            pairs.append((u, v) if u < v else (v, u))
    uniq = [s for s in groups if len(s) > 7]
    freq = Counter(chain.from_iterable(uniq))
    order = sorted(freq, key=freq.get)
    rank = dict(zip(order, range(len(order))))
    n1 = 0
    for t in order:
        if freq[t] > 1:
            break
        n1 += 1
    uniq.sort(key=len)
    sizes = [len(s) for s in uniq]
    index = {}
    get = index.get
    big = {}
    bget = big.get
    for xi, s in enumerate(uniq):
        a = sizes[xi]
        ids = sorted(map(rank.get, s))
        minb = (4 * a + 4) // 5
        p = a - minb
        if ids[p] < n1:
            continue
        if a < 16:
            cands = None
            for t in ids[:p + 1]:
                if t >= n1:
                    lst = get(t)
                    if lst:
                        if cands is None:
                            cands = set(lst)
                        else:
                            cands.update(lst)
            if cands:
                for yi in cands:
                    y = uniq[yi]
                    b = sizes[yi]
                    if b >= minb and 9 * len(s & y) >= 4 * (a + b):
                        for u in groups[s]:
                            for v in groups[y]:
                                pairs.append((u, v) if u < v else (v, u))
        else:
            cnt = {}
            cget = cnt.get
            for i in range(p + 1):
                t = ids[i]
                if t < n1:
                    continue
                lst = get(t)
                if lst:
                    for yi in lst:
                        if sizes[yi] >= minb and cget(yi, 0) >= 0:
                            cnt[yi] = cget(yi, 0) + 1
                lst = bget(t)
                if lst:
                    ra = a - i
                    for yi, j in lst:
                        c = cget(yi, 0)
                        if c < 0:
                            continue
                        b = sizes[yi]
                        if b < minb:
                            continue
                        need = (4 * (a + b) + 8) // 9
                        rb = b - j
                        if c + (ra if ra < rb else rb) < need:
                            cnt[yi] = -1
                        else:
                            cnt[yi] = c + 1
            for yi, c in cnt.items():
                if c > 0:
                    y = uniq[yi]
                    b = sizes[yi]
                    if 9 * len(s & y) >= 4 * (a + b):
                        for u in groups[s]:
                            for v in groups[y]:
                                pairs.append((u, v) if u < v else (v, u))
        if a < 16:
            for t in ids[:a - (8 * a + 8) // 9 + 1]:
                if t >= n1:
                    lst = get(t)
                    if lst is None:
                        index[t] = [xi]
                    else:
                        lst.append(xi)
        else:
            for j in range(a - (8 * a + 8) // 9 + 1):
                t = ids[j]
                if t >= n1:
                    lst = bget(t)
                    if lst is None:
                        big[t] = [(xi, j)]
                    else:
                        lst.append((xi, j))
    return pairs
