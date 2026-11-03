from collections import Counter
from itertools import chain


def near_duplicates(records):
    groups = {}
    for i, r in enumerate(records):
        s = frozenset(r.split())
        if s:
            g = groups.get(s)
            if g is None:
                groups[s] = [i]
            else:
                g.append(i)
    pairs = []
    keys = list(groups)
    for s in keys:
        g = groups[s]
        if len(g) > 1:
            for a in range(len(g)):
                ga = g[a]
                for b in g[a + 1:]:
                    pairs.append((ga, b))
    # a set of at most 3 tokens can only match an identical set
    keys.sort(key=len)
    sizes = list(map(len, keys))
    u0 = 0
    while u0 < len(sizes) and sizes[u0] < 4:
        u0 += 1
    freq = Counter(chain.from_iterable(keys[u0:]))
    rk = dict(zip(sorted(freq, key=freq.get), range(len(freq))))
    rg = rk.get
    index = {}
    ig = index.get
    for u in range(u0, len(keys)):
        s = keys[u]
        n = sizes[u]
        x = sorted(s, key=rg)
        minm = (4 * n + 4) // 5
        # up to 8 tokens, two distinct sets of one size never reach 0.8
        mx = n if n > 8 else n - 1
        pi = n - (8 * n + 8) // 9 + 1
        cands = None
        for i in range(n - minm + 1):
            t = x[i]
            lst = ig(t)
            if lst is None:
                if i < pi:
                    index[t] = [(u, n, i)]
                continue
            if cands is None:
                cands = {}
            rest = n - i
            for v, m, j in lst:
                if m < minm or m > mx or v in cands:
                    continue
                b = m - j
                if rest < b:
                    b = rest
                cands[v] = m if 9 * b >= 4 * (n + m) else 0
            if i < pi:
                lst.append((u, n, i))
        if cands:
            gu = groups[s]
            for v, m in cands.items():
                if m and 9 * len(s & keys[v]) >= 4 * (n + m):
                    for a in groups[keys[v]]:
                        for b in gu:
                            pairs.append((a, b) if a < b else (b, a))
    return pairs
