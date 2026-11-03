from collections import Counter
from itertools import chain


def near_duplicates(records):
    groups = {}
    sd = groups.setdefault
    i = 0
    for s in map(frozenset, map(str.split, records)):
        sd(s, []).append(i)
        i += 1
    groups.pop(frozenset(), None)
    gget = groups.get
    pairs = []
    append = pairs.append
    big = []
    for s, g in groups.items():
        if len(g) > 1:
            for x in range(len(g)):
                gx = g[x]
                for y in g[x + 1:]:
                    append((gx, y))
        n = len(s)
        if n > 7:
            big.append(s)
        if 4 < n < 9:
            # below 9 tokens a match is always this set minus one token
            for t in s:
                h = gget(s.difference((t,)))
                if h is not None:
                    for i in g:
                        for j in h:
                            append((i, j) if i < j else (j, i))
    if not big:
        return pairs
    freq = Counter(chain.from_iterable(big))
    rget = dict(zip(sorted(freq, key=freq.get), range(len(freq)))).get
    big.sort(key=len)
    lens = list(map(len, big))
    index = {}
    iget = index.get
    k = 0
    for s in big:
        n = lens[k]
        toks = sorted(map(rget, s))
        if n > 8:
            minlen = (4 * n + 4) // 5
            cands = set()
            for t in toks[:n - minlen + 1]:
                lst = iget(t)
                if lst is not None:
                    cands.update(lst)
            if cands:
                lim = 4 * n
                for c in cands:
                    m = lens[c]
                    if m >= minlen and 9 * len(s & big[c]) >= lim + 4 * m:
                        for i in groups[s]:
                            for j in groups[big[c]]:
                                append((i, j) if i < j else (j, i))
        for t in toks[:n - (8 * n + 8) // 9 + 1]:
            lst = iget(t)
            if lst is None:
                index[t] = [k]
            else:
                lst.append(k)
        k += 1
    return pairs
