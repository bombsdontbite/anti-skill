from collections import Counter
from itertools import chain


def near_duplicates(records):
    S = list(map(frozenset, map(str.split, records)))
    last = dict(zip(S, range(len(S))))
    empty = frozenset()
    last.pop(empty, None)
    pairs = []
    dups = None
    if len(last) + S.count(empty) < len(S):
        dups = {}
        lget = last.get
        for i, s in enumerate(S):
            j = lget(s)
            if j is not None and j != i:
                g = dups.get(s)
                if g is None:
                    dups[s] = g = [j]
                for y in g:
                    pairs.append((i, y) if i < y else (y, i))
                g.append(i)
    freq = Counter(chain.from_iterable(last))
    order = sorted([t for t, c in freq.items() if c > 1], key=freq.get)
    rank = dict.fromkeys(freq, -1)
    rank.update(zip(order, range(len(order))))
    rget = rank.get
    sets = sorted(last, key=len)
    lens = list(map(len, sets))
    index = {}
    iget = index.get
    start = {}
    for k, s in enumerate(sets):
        n = lens[k]
        minlen = (4 * n + 4) // 5
        p = n - minlen + 1
        if p == 1:
            m = min(map(rget, s))
            if m < 0:
                continue
            pref = (m,)
        else:
            pref = sorted(map(rget, s))[:p]
            if pref[-1] < 0:
                continue
        cands = None
        q = n - (8 * n + 8) // 9 + 1
        for t in pref:
            if t < 0:
                q -= 1
                continue
            lst = iget(t)
            if lst is None:
                if q > 0:
                    index[t] = [k]
                    start[t] = 0
            else:
                st = start[t]
                L = len(lst)
                while st < L and lens[lst[st]] < minlen:
                    st += 1
                start[t] = st
                if st < L:
                    if cands is None:
                        cands = set(lst[st:])
                    else:
                        cands.update(lst[st:])
                if q > 0:
                    lst.append(k)
            q -= 1
        if cands:
            for c in cands:
                b = sets[c]
                if 9 * len(s & b) >= 4 * (n + lens[c]):
                    if dups is None:
                        i = last[s]
                        j = last[b]
                        pairs.append((i, j) if i < j else (j, i))
                    else:
                        for i in dups.get(s) or (last[s],):
                            for j in dups.get(b) or (last[b],):
                                pairs.append((i, j) if i < j else (j, i))
    return pairs
