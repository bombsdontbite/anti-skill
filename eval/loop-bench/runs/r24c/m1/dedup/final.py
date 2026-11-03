from bisect import bisect_left
from itertools import chain, combinations


def near_duplicates(records, stride=4):
    sets = list(map(frozenset, map(str.split, records)))
    nrec = len(sets)
    first = dict(zip(reversed(sets), range(nrec - 1, -1, -1)))
    first.pop(frozenset(), None)
    extra = {}
    if len(first) < nrec:
        for i in sorted(set(range(nrec)).difference(first.values())):
            s = sets[i]
            if s:
                g = extra.get(s)
                if g is None:
                    extra[s] = [first[s], i]
                else:
                    g.append(i)
    pairs = []
    for g in extra.values():
        pairs.extend(combinations(g, 2))
    uniq = sorted(first, key=len)
    lens = list(map(len, uniq))
    lo = bisect_left(lens, 4)
    uniq = uniq[lo:]
    lens = lens[lo:]
    freq = dict.fromkeys(chain.from_iterable(uniq), 0)
    for t in chain.from_iterable(uniq[::stride]):
        freq[t] += 1
    order = sorted(freq, key=freq.get)
    top = lens[-1] + 1 if lens else 0
    MIN = [(4 * n + 4) // 5 for n in range(top)]
    P = [n - MIN[n] + 1 for n in range(top)]
    Q = [n - (8 * n + 8) // 9 + 1 for n in range(top)]
    rk = dict(zip(order, range(len(order)))).get
    index = {}
    get = index.get
    for k, s in enumerate(uniq):
        n = lens[k]
        minlen = MIN[n]
        p = P[n]
        q = Q[n]
        toks = sorted(s, key=rk)
        cands = set()
        for t in toks[:q]:
            lst = get(t)
            if lst is None:
                index[t] = [k]
            else:
                cands.update(lst)
                lst.append(k)
        for t in toks[q:p]:
            lst = get(t)
            if lst is not None:
                cands.update(lst)
        if cands:
            for c in cands:
                m = lens[c]
                if m < minlen:
                    continue
                o = uniq[c]
                inter = len(s & o)
                if 5 * inter >= 4 * (n + m - inter):
                    ga = extra.get(s) or (first[s],)
                    gb = extra.get(o) or (first[o],)
                    for a in ga:
                        for b in gb:
                            pairs.append((a, b) if a < b else (b, a))
    return pairs
