from collections import Counter
from itertools import chain


def near_duplicates(records):
    sets = list(map(frozenset, map(str.split, records)))
    last = {s: i for i, s in enumerate(sets)}
    last.pop(frozenset(), None)
    keys = list(last)
    pairs = []
    groups = {}
    if len(last) < len(sets):
        lget = last.get
        for i in [i for i, s in enumerate(sets) if lget(s, i) != i]:
            s = sets[i]
            if s in groups:
                groups[s].append(i)
            else:
                groups[s] = [i]
        for s, g in groups.items():
            g.append(last[s])
            n = len(g)
            for x in range(n):
                gx = g[x]
                for y in range(x + 1, n):
                    pairs.append((gx, g[y]))
    keys.sort(key=len)
    lens = list(map(len, keys))
    s0 = 0
    while s0 < len(lens) and lens[s0] < 4:
        s0 += 1
    freq = Counter(chain.from_iterable(keys[s0:]))
    fget = freq.get
    rank = {t: r for r, t in enumerate(sorted(freq, key=fget))}
    get = rank.get
    index = {}
    iget = index.get
    top = lens[-1] + 1 if lens else 1
    ML = [(4 * n + 4) // 5 for n in range(top)]
    QL = [n - (8 * n + 8) // 9 + 1 for n in range(top)]
    for ai in range(s0, len(keys)):
        a = keys[ai]
        la = lens[ai]
        if la == 4:
            t = min(a, key=get)
            lst = iget(t)
            if lst is None:
                index[t] = [ai]
            else:
                lst.append(ai)
            continue
        minlen = ML[la]
        q = QL[la]
        toks = sorted(a, key=get)
        cand = set()
        for t in toks[:la - minlen + 1]:
            lst = iget(t)
            if lst is None:
                if q:
                    index[t] = [ai]
            else:
                if lst and lens[lst[0]] < minlen:
                    n = 1
                    while n < len(lst) and lens[lst[n]] < minlen:
                        n += 1
                    del lst[:n]
                cand.update(lst)
                if q:
                    lst.append(ai)
            if q:
                q -= 1
        for bi in cand:
            b = keys[bi]
            lb = lens[bi]
            inter = len(a & b)
            if 5 * inter >= 4 * (la + lb - inter):
                i = last[a]
                j = last[b]
                if groups and (a in groups or b in groups):
                    for i in groups.get(a) or (i,):
                        for j in groups.get(b) or (j,):
                            pairs.append((i, j) if i < j else (j, i))
                else:
                    pairs.append((i, j) if i < j else (j, i))
    return pairs
