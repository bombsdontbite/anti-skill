from collections import Counter
from itertools import chain


def near_duplicates(records):
    groups = {}
    multi = []
    for i, s in enumerate(map(frozenset, map(str.split, records))):
        g = groups.get(s)
        if g is None:
            groups[s] = [i]
        else:
            if len(g) == 1:
                multi.append(g)
            g.append(i)
    empty = groups.pop(frozenset(), None)
    pairs = []
    for g in multi:
        if g is not empty:
            for a in range(len(g)):
                ga = g[a]
                for b in g[a + 1:]:
                    pairs.append((ga, b))
    # 9|A & B| >= 4(|A| + |B|): a set of 3 tokens or fewer only matches an equal set, one of 4
    # an equal set or a superset of 5, one of 8 or fewer an equal set or a superset.
    uniq = [s for s in groups if len(s) > 3]
    cnt = Counter(chain.from_iterable(uniq))
    order = sorted(cnt, key=cnt.get)
    key = dict(zip(order, range(len(order)))).get
    uniq.sort(key=len)
    index = {}
    iget = index.get
    hits = set()
    add = hits.add
    lo = 0
    for n, c in sorted(Counter(map(len, uniq)).items()):
        hi = lo + c
        bucket = uniq[lo:hi]
        lo = hi
        if n == 4:
            for s in bucket:
                t = min(s, key=key)
                lst = iget(t)
                if lst is None:
                    index[t] = [s]
                else:
                    lst.append(s)
            continue
        minlen = (4 * n + 4) // 5
        if n <= 8:
            # p = 2 probe tokens, q = 1 indexed.
            for s in bucket:
                t, u = sorted(s, key=key)[:2]
                lst = iget(t)
                if lst is None:
                    index[t] = [s]
                else:
                    for y in lst:
                        if y < s and len(y) >= minlen:
                            add((s, y))
                    lst.append(s)
                lst = iget(u)
                if lst is not None:
                    for y in lst:
                        if y < s and len(y) >= minlen:
                            add((s, y))
            continue
        p = n - minlen + 1
        q = n - (8 * n + 8) // 9 + 1
        for s in bucket:
            pre = sorted(s, key=key)
            for t in pre[:q]:
                lst = iget(t)
                if lst is None:
                    index[t] = [s]
                else:
                    for y in lst:
                        m = len(y)
                        if m >= minlen:
                            inter = len(s & y)
                            if 5 * inter >= 4 * (n + m - inter):
                                add((s, y))
                    lst.append(s)
            for t in pre[q:p]:
                lst = iget(t)
                if lst is not None:
                    for y in lst:
                        m = len(y)
                        if m >= minlen:
                            inter = len(s & y)
                            if 5 * inter >= 4 * (n + m - inter):
                                add((s, y))
    for s, y in hits:
        gy = groups[y]
        for i in groups[s]:
            for j in gy:
                pairs.append((i, j) if i < j else (j, i))
    return pairs
