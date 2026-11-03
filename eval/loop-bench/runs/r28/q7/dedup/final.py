from collections import Counter
from itertools import chain, count


def near_duplicates(records):
    groups = {}
    for i, s in enumerate(map(frozenset, map(str.split, records))):
        if s:
            g = groups.get(s)
            if g is None:
                groups[s] = [i]
            else:
                g.append(i)
    pairs = []
    sets = sorted(groups, key=len)
    for g in groups.values():
        if len(g) > 1:
            for a in range(len(g)):
                ga = g[a]
                for b in range(a + 1, len(g)):
                    pairs.append((ga, g[b]))
    # prefix filtering: any consistent token order is correct, rare tokens first keeps candidates few
    freq = Counter(chain.from_iterable(sets))
    rank = dict(zip(sorted(freq, key=freq.__getitem__), count()))
    key = rank.__getitem__
    index = {}
    get = index.get
    lens = []
    for x, s in enumerate(sets):
        n = len(s)
        lens.append(n)
        minlen = (4 * n + 4) // 5
        # distinct sets of equal size below 9 are never 80 % alike
        small = n if n < 9 else 0
        if minlen == n:
            t = min(s, key=key)
            lst = get(t)
            if lst is None:
                index[t] = [x]
                continue
            cands = lst[:]
            lst.append(x)
        else:
            toks = sorted(s, key=key)
            q = n - (8 * n + 8) // 9 + 1
            cands = set()
            for k in range(n - minlen + 1):
                t = toks[k]
                lst = get(t)
                if lst is None:
                    if k < q:
                        index[t] = [x]
                else:
                    cands.update(lst)
                    if k < q:
                        lst.append(x)
        if cands:
            gx = groups[s]
            for y in cands:
                m = lens[y]
                if m < minlen or m == small:
                    continue
                sy = sets[y]
                if 9 * len(s & sy) >= 4 * (n + m):
                    for a in gx:
                        for b in groups[sy]:
                            pairs.append((a, b) if a < b else (b, a))
    return pairs
