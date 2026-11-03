from collections import Counter
from itertools import chain


def near_duplicates(records):
    groups = {}
    pairs = []
    append = pairs.append
    big = []
    mid = []
    hs = {}
    for i, s in enumerate(map(frozenset, map(str.split, records))):
        g = groups.get(s)
        if g is None:
            groups[s] = [i]
            la = len(s)
            # Sets of 3 or fewer tokens only match identical sets; up to 7 the only other
            # match is a superset with one more token, found by hash sums. Size 8+ goes to
            # prefix filtering.
            if la > 3:
                if la > 7:
                    big.append(s)
                    if la > 8:
                        continue
                h = sum(map(hash, s))
                if la < 8:
                    o = hs.get(h)
                    if o is None:
                        hs[h] = [s]
                    else:
                        o.append(s)
                if la > 4:
                    mid.append((s, h))
        elif s:
            for j in g:
                append((j, i))
            g.append(i)
    for s, h in mid:
        lb = len(s) - 1
        for d in map(hash, s):
            o = hs.get(h - d)
            if o is not None:
                for a in o:
                    if len(a) == lb and a < s:
                        for x1 in groups[s]:
                            for y1 in groups[a]:
                                append((x1, y1) if x1 < y1 else (y1, x1))
    if len(big) < 2:
        return pairs
    # Prefix filtering (rarest tokens first) with PPJoin's positional filter.
    freq = Counter(chain.from_iterable(big))
    order = sorted(freq, key=freq.__getitem__)
    key = dict(zip(order, range(len(order)))).__getitem__
    big.sort(key=len)
    index = {}
    lens = []
    k = 0
    for s in big:
        la = len(s)
        minlen = (4 * la + 4) // 5
        p = la - minlen + 1
        q = la - (8 * la + 8) // 9 + 1
        seen = set()
        x = 0
        for t in sorted(s, key=key)[:p]:
            lst = index.get(t)
            if lst is not None:
                for c, y in lst:
                    if c not in seen:
                        seen.add(c)
                        lc = lens[c]
                        if lc >= minlen:
                            tot = 4 * (la + lc)
                            r = la - x if la - x < lc - y else lc - y
                            if 9 * r >= tot:
                                cs = big[c]
                                if 9 * len(s & cs) >= tot:
                                    for x1 in groups[s]:
                                        for y1 in groups[cs]:
                                            append((x1, y1) if x1 < y1 else (y1, x1))
            if x < q:
                if lst is None:
                    index[t] = [(k, x)]
                else:
                    lst.append((k, x))
            x += 1
        lens.append(la)
        k += 1
    return pairs
