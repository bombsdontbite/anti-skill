from collections import Counter
from itertools import chain


def near_duplicates(records):
    sets = list(map(frozenset, map(str.split, records)))
    cnt = Counter(chain.from_iterable(sets))
    rank = {t: k for k, t in enumerate(sorted(cnt, key=cnt.get))}
    rget = rank.get
    sizes = list(map(len, sets))
    buckets = {}
    for i, n in enumerate(sizes):
        b = buckets.get(n)
        if b is None:
            buckets[n] = [i]
        else:
            b.append(i)
    buckets.pop(0, None)
    index = {}
    iget = index.get
    pairs = []
    add = pairs.append
    for n in sorted(buckets):
        minsize = (4 * n + 4) // 5
        p = n - minsize + 1
        q = n - (8 * n + 8) // 9 + 1
        if n < 5:
            # same size forced, and 80 % of at most 4 tokens means identical
            same = {}
            sget = same.get
            for x in buckets[n]:
                a = sets[x]
                g = sget(a)
                if g is None:
                    same[a] = [x]
                else:
                    for y in g:
                        add((y, x))
                    g.append(x)
                if n == 4:
                    t = min(a, key=rget)
                    lst = iget(t)
                    if lst is None:
                        index[t] = [x]
                    else:
                        lst.append(x)
            continue
        for x in buckets[n]:
            a = sets[x]
            toks = sorted(a, key=rget)
            cands = set()
            for t in toks[:p]:
                lst = iget(t)
                if lst:
                    while sizes[lst[0]] < minsize:
                        del lst[0]
                        if not lst:
                            break
                    cands.update(lst)
            for y in cands:
                if 9 * len(a & sets[y]) >= 4 * (n + sizes[y]):
                    add((y, x) if y < x else (x, y))
            for t in toks[:q]:
                lst = iget(t)
                if lst is None:
                    index[t] = [x]
                else:
                    lst.append(x)
    return pairs
