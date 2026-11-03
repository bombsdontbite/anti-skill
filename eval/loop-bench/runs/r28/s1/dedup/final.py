from collections import Counter
from itertools import chain, combinations, product, repeat


def near_duplicates(records):
    groups = {}
    for i, s in enumerate(map(frozenset, map(str.split, records))):
        g = groups.get(s)
        if g is None:
            groups[s] = [i]
        else:
            g.append(i)
    groups.pop(frozenset(), None)
    uniq = sorted(groups, key=len)
    pairs = []
    for g in groups.values():
        if len(g) > 1:
            pairs.extend(combinations(g, 2))
    freq = Counter(chain.from_iterable(uniq))
    rank = dict(zip(sorted(freq, key=freq.__getitem__), range(len(freq))))
    index = {}
    get = index.get
    append = pairs.append
    rk = rank.__getitem__
    # ranks below `single` belong to tokens found in one record only
    single = list(freq.values()).count(1)
    x = 0
    for a in uniq:
        n = len(a)
        if n < 5:
            t = min(map(rk, a))
            if t < single:
                x += 1
                continue
            lst = get(t)
            if lst is None:
                index[t] = [x]
                x += 1
                continue
            cand = set(lst)
            lst.append(x)
        else:
            toks = sorted(map(rk, a))
            pp = n - (4 * n + 4) // 5 + 1
            if toks[pp - 1] < single:
                x += 1
                continue
            pi = n - (8 * n + 8) // 9 + 1
            cand = set()
            k = 0
            for t in toks[:pp]:
                lst = get(t)
                if lst is None:
                    if k < pi:
                        index[t] = [x]
                else:
                    cand.update(lst)
                    if k < pi:
                        lst.append(x)
                k += 1
        if cand:
            ga = groups[a]
            n4 = 4 * n
            for y in cand:
                b = uniq[y]
                m = len(b)
                if 5 * m >= n4 and 9 * len(a & b) >= n4 + 4 * m:
                    gb = groups[b]
                    if len(ga) == 1 and len(gb) == 1:
                        i = ga[0]; j = gb[0]
                        append((i, j) if i < j else (j, i))
                    else:
                        for i, j in product(ga, gb):
                            append((i, j) if i < j else (j, i))
        x += 1
    return pairs
