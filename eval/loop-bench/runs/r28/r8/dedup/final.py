from collections import Counter
from itertools import chain


def near_duplicates(records):
    sets = list(map(frozenset, map(str.split, records)))
    last = dict(zip(sets, range(len(sets))))
    last.pop(frozenset(), None)
    pairs = []
    app = pairs.append
    extra = {}
    if len(last) < len(sets):
        for i, s in enumerate(sets):
            if s:
                r = last[s]
                if r != i:
                    g = extra.get(r)
                    if g is None:
                        extra[r] = [i, r]
                    else:
                        g.insert(-1, i)
        for g in extra.values():
            for x in range(len(g)):
                for y in range(x + 1, len(g)):
                    app((g[x], g[y]))
    keys = sorted(last, key=len)
    ids = [last[a] for a in keys]
    freq = Counter(chain.from_iterable(keys))
    order = sorted(freq, key=freq.get)
    rank = {t: k for k, t in enumerate(order)}
    rk = rank.get
    once = 0
    for t in order:
        if freq[t] > 1:
            break
        once += 1
    lens = list(map(len, keys))
    index = [None] * len(order)
    start = [0] * len(order)
    tokl = [None] * len(keys)
    sigs = [0] * len(keys)
    for k, a in enumerate(keys):
        n = lens[k]
        minlen = (4 * n + 4) // 5
        p = n - minlen + 1
        q = n - (8 * n + 8) // 9 + 1
        toks = tokl[k] = sorted(map(rk, a))
        cand = set()
        for c, t in enumerate(toks[:p]):
            if t < once:
                continue
            lst = index[t]
            if lst:
                s = start[t]
                m = len(lst)
                if s < m and lens[lst[s]] < minlen:
                    s += 1
                    while s < m and lens[lst[s]] < minlen:
                        s += 1
                    start[t] = s
                if s:
                    cand.update(lst[s:])
                else:
                    cand.update(lst)
                if c < q:
                    lst.append(k)
            elif c < q:
                index[t] = [k]
        lim = 4 * n
        if n >= 15 and len(cand) > 2:
            sig = 0
            for t in toks:
                sig |= 1 << (t & 255)
            sigs[k] = sig
            n5 = 5 * n
            keep = []
            for j in cand:
                sj = sigs[j]
                if not sj:
                    for t in tokl[j]:
                        sj |= 1 << (t & 255)
                    sigs[j] = sj
                if 9 * (sig | sj).bit_count() <= n5 + 5 * lens[j]:
                    keep.append(j)
            cand = keep
        for j in cand:
            if 9 * len(a & keys[j]) >= lim + 4 * lens[j]:
                x = ids[k]
                y = ids[j]
                if x in extra or y in extra:
                    for x in extra.get(x, (x,)):
                        for y in extra.get(y, (y,)):
                            app((x, y) if x < y else (y, x))
                else:
                    app((x, y) if x < y else (y, x))
    return pairs
