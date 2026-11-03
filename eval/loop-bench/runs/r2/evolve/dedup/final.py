from collections import Counter
from itertools import chain, compress, repeat
from operator import sub

# Distinct sets of size <= 3 never pair; between distinct sets of size <= 8 the only pairs are
# y < x with |y| = |x| - 1 (hash-sum lookups); sets of size >= 8 go through prefix filtering.


def near_duplicates(records):
    groups = {}
    pairs = []
    app = pairs.append
    for i, f in enumerate(map(frozenset, map(str.split, records))):
        g = groups.get(f)
        if g is None:
            groups[f] = [i]
        else:
            if f:
                for j in g:
                    app((j, i))
            g.append(i)
    groups.pop(frozenset(), None)
    sets = sorted([f for f in groups if len(f) > 3], key=len)
    sizes = list(map(len, sets))
    span = {}
    start = 0
    for a, c in sorted(Counter(sizes).items()):
        span[a] = (start, start + c)
        start += c
    hits = []
    hit = hits.append
    prev = None
    for a in range(4, 9):
        if a not in span:
            prev = None
            continue
        chunk = sets[span[a][0]:span[a][1]]
        H = list(map(hash, chain.from_iterable(chunk)))
        hs = list(map(sum, zip(*[iter(H)] * a)))
        if prev is not None:
            res = list(map(prev.get, map(sub, chain.from_iterable(map(repeat, hs, repeat(a))), H)))
            for k in compress(range(len(res)), res):
                hit((chunk[k // a], res[k]))
        prev = dict(zip(hs, chunk))
        if len(prev) < len(chunk):  # hash-sum collision: exact one-deletion lookups instead
            prev = None
            if a < 8 and a + 1 in span:
                for x in sets[span[a + 1][0]:span[a + 1][1]]:
                    for t in x:
                        if x - {t} in groups:
                            hit((x, x - {t}))
    lo = min([span[a][0] for a in span if a >= 8], default=start)
    big = sets[lo:]
    if len(big) > 1 and len(big[-1]) > 8:
        bsz = sizes[lo:]
        df = Counter(chain.from_iterable(big))
        rg = dict(zip(sorted(df, key=df.get), range(len(df)))).get
        need = [-(-4 * a // 5) for a in range(bsz[-1] + 1)]
        pref = [sorted(map(rg, s))[:a - need[a] + 1] for s, a in zip(big, bsz)]
        multi = {t for t, c in Counter(chain.from_iterable(pref)).items() if c > 1}
        isd = multi.isdisjoint
        index = {}
        ig = index.get
        for p in range(len(big)):
            tk = pref[p]
            if isd(tk):
                continue
            a = bsz[p]
            if a > 8:
                cands = set()
                for t in tk:
                    lst = ig(t)
                    if lst:
                        cands.update(lst)
                s = big[p]
                for q in cands:
                    b = bsz[q]
                    if b >= need[a] and 9 * len(s & big[q]) >= 4 * (a + b):
                        hit((s, big[q]))
            for t in tk[:a - (-(-8 * a // 9)) + 1]:
                if t in multi:
                    lst = ig(t)
                    if lst is None:
                        index[t] = [p]
                    else:
                        lst.append(p)
    for x, y in hits:
        if len(x) > 8 or y < x:
            for u in groups[x]:
                for v in groups[y]:
                    app((u, v) if u < v else (v, u))
    return pairs
