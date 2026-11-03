from collections import Counter
from itertools import chain


def near_duplicates(records):
    groups = {}
    sd = groups.setdefault
    for i, s in enumerate(map(frozenset, map(str.split, records))):
        sd(s, []).append(i)
    groups.pop(frozenset(), None)
    pairs = []
    for g in groups.values():
        if len(g) > 1:
            for x in range(len(g)):
                gx = g[x]
                for y in g[x + 1:]:
                    pairs.append((gx, y))
    keys = [k for k in groups if len(k) > 3]
    keys.sort(key=len)
    freq = Counter(chain.from_iterable(keys))
    rank = {t: r for r, t in enumerate(sorted(freq, key=freq.__getitem__))}
    rk = rank.__getitem__
    index = {}
    get = index.get
    isd = index.setdefault
    if len(keys) and sum(map(len, keys)) < 20 * len(keys):
        for k in keys:
            a = len(k)
            toks = sorted(k, key=rk)
            minb = (4 * a + 4) // 5
            q = a - (8 * a + 8) // 9 + 1
            cands = None
            if a == 4:
                for t in toks[:1]:
                    isd(t, []).append(k)
                continue
            for t in toks[:a - minb + 1]:
                lst = get(t)
                if lst:
                    if cands is None:
                        cands = set(lst)
                    else:
                        cands.update(lst)
            for t in toks[:q]:
                isd(t, []).append(k)
            if cands:
                g = groups[k]
                for o in cands:
                    b = len(o)
                    if b >= minb and 9 * len(k & o) >= 4 * (a + b):
                        for i in g:
                            for j in groups[o]:
                                pairs.append((i, j) if i < j else (j, i))
    else:
        for k in keys:
            a = len(k)
            if a == 4:
                isd(min(k, key=rk), []).append((k, 0))
                continue
            toks = sorted(k, key=rk)
            minb = (4 * a + 4) // 5
            cnt = {}
            cg = cnt.get
            i = a
            for t in toks[:a - minb + 1]:
                i -= 1
                lst = get(t)
                if lst:
                    for o, j in lst:
                        b = len(o)
                        if b < minb:
                            continue
                        c = cg(o, 0)
                        if c < 0:
                            continue
                        j = b - j - 1
                        if c + 1 + (i if i < j else j) >= (4 * (a + b) + 8) // 9:
                            cnt[o] = c + 1
                        else:
                            cnt[o] = -1
            j = 0
            for t in toks[:a - (8 * a + 8) // 9 + 1]:
                isd(t, []).append((k, j))
                j += 1
            if cnt:
                g = groups[k]
                for o, c in cnt.items():
                    if c > 0 and 9 * len(k & o) >= 4 * (a + len(o)):
                        for i in g:
                            for j in groups[o]:
                                pairs.append((i, j) if i < j else (j, i))
    return pairs
