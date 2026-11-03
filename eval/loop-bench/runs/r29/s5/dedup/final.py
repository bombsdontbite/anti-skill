from collections import Counter
from itertools import chain


def near_duplicates(records):
    sets = list(map(frozenset, map(str.split, records)))
    last = dict(zip(sets, range(len(sets))))
    pairs = []
    groups = {}
    if len(last) != len(sets):
        for i in [i for i, s in enumerate(sets) if last[s] != i]:
            g = groups.get(sets[i])
            if g is None:
                groups[sets[i]] = [i]
            else:
                g.append(i)
        groups.pop(frozenset(), None)
        for s, g in groups.items():
            g.append(last[s])
            for a in range(len(g)):
                ga = g[a]
                for b in range(a + 1, len(g)):
                    pairs.append((ga, g[b]))
    gget = groups.get
    # sets of 3 or fewer tokens only match identical sets
    uniq = [s for s in last if len(s) > 3]
    if len(uniq) < 2:
        return pairs
    uniq.sort(key=len)
    freq = Counter(chain.from_iterable(uniq))
    multi = [t for t, c in freq.items() if c > 1]
    multi.sort(key=freq.get)
    # tokens in no other set rank -1: first in the order, and they never match
    rank = dict.fromkeys(freq, -1)
    rank.update(zip(multi, range(len(multi))))
    rget = rank.get
    index = {}
    iget = index.get
    lens = list(map(len, uniq))
    start = {}
    sget = start.get
    for x, s in enumerate(uniq):
        n = lens[x]
        minlen = (4 * n + 4) // 5
        toks = sorted(map(rget, s))
        ones = toks.count(-1)
        if ones > n - minlen:
            continue
        cands = set()
        for t in toks[ones:n - minlen + 1]:
            lst = iget(t)
            if lst is not None:
                k = sget(t, 0)
                if k < len(lst) and lens[lst[k]] < minlen:
                    k += 1
                    while k < len(lst) and lens[lst[k]] < minlen:
                        k += 1
                    start[t] = k
                cands.update(lst[k:] if k else lst)
        for y in cands:
            sy = uniq[y]
            inter = len(s & sy)
            if 5 * inter >= 4 * (n + lens[y] - inter):
                gx = gget(s)
                gy = gget(sy)
                if gx is None and gy is None:
                    i, j = last[s], last[sy]
                    pairs.append((i, j) if i < j else (j, i))
                else:
                    for i in gx or (last[s],):
                        for j in gy or (last[sy],):
                            pairs.append((i, j) if i < j else (j, i))
        for t in toks[ones:n - (8 * n + 8) // 9 + 1]:
            lst = iget(t)
            if lst is None:
                index[t] = [x]
            else:
                lst.append(x)
    return pairs
