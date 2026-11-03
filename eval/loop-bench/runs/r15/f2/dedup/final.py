from collections import Counter
from itertools import chain


def near_duplicates(records):
    words = list(map(str.split, records))
    freq = Counter(chain.from_iterable(words))
    rank = dict(zip(sorted(freq, key=freq.get), range(len(freq))))
    rget = rank.get
    # sorted tuples of ints: the collector stops tracking them, unlike sets
    recs = [tuple(sorted(set(map(rget, w)))) for w in words]
    del words
    # ranks below u belong to words seen once, which no other record can share
    u = list(freq.values()).count(1)
    lens = list(map(len, recs))
    bylen = {}
    for i, n in enumerate(lens):
        g = bylen.get(n)
        if g is None:
            bylen[n] = [i]
        else:
            g.append(i)
    bylen.pop(0, None)
    # word -> ids of records indexed under it; records arrive by size, so ids stay sorted by size
    index = [None] * len(rank)
    pairs = []
    add = pairs.append
    for n in sorted(bylen):
        group = bylen[n]
        if n < 5:
            # prefix of one word; partners must have the same size
            for i in group:
                toks = recs[i]
                w = toks[0]
                if w < u:
                    continue
                ids = index[w]
                if ids is None:
                    index[w] = [i]
                    continue
                if ids and lens[ids[0]] < n:
                    t = 1
                    while t < len(ids) and lens[ids[t]] < n:
                        t += 1
                    del ids[:t]
                if ids:
                    s = set(toks)
                    for j in ids:
                        inter = len(s.intersection(recs[j]))
                        if 5 * inter >= 4 * (n + lens[j] - inter):
                            add((j, i) if j < i else (i, j))
                ids.append(i)
            continue
        m = (4 * n + 4) // 5
        p = n - m + 1
        q = n - (8 * n + 8) // 9 + 1
        for i in group:
            toks = recs[i]
            if toks[p - 1] < u:
                continue
            cand = None
            k = 0
            for w in toks[:p]:
                if w < u:
                    k += 1
                    continue
                ids = index[w]
                if ids is None:
                    if k < q:
                        index[w] = [i]
                else:
                    if ids and lens[ids[0]] < m:
                        t = 1
                        while t < len(ids) and lens[ids[t]] < m:
                            t += 1
                        del ids[:t]
                    if ids:
                        if cand is None:
                            cand = set(ids)
                        else:
                            cand.update(ids)
                    if k < q:
                        ids.append(i)
                k += 1
            if cand:
                s = set(toks)
                for j in cand:
                    inter = len(s.intersection(recs[j]))
                    if 5 * inter >= 4 * (n + lens[j] - inter):
                        add((j, i) if j < i else (i, j))
    return pairs
