# bisect is written out here, which saves importing the module
from itertools import chain, combinations, compress, count, repeat
from operator import sub


def bisect_left(a, x):
    lo = 0
    hi = len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo


def near_duplicates(records):
    groups = {}
    for i, s in enumerate(map(frozenset, map(str.split, records))):
        g = groups.get(s)
        if g is None:
            groups[s] = [i]
        else:
            g.append(i)
    groups.pop(frozenset(), None)
    pairs = []
    add = pairs.append
    for g in groups.values():
        if len(g) > 1:
            pairs.extend(combinations(g, 2))
    uniq = sorted(groups, key=len)
    if not uniq:
        return pairs
    lens = list(map(len, uniq))
    # Two different sets of sizes m <= n are 80 % alike only if 5m - 4n >= 9 * |B - A|, so
    # below 9 tokens the smaller one is the larger minus exactly one token, and sets of up to
    # 3 tokens match only identical ones. A set minus a token is found by the sum of token
    # hashes, a whole size class at a time; set p // n owns position p of the deletions.
    gget = groups.get
    prev = {}
    clash = False
    for n in range(4, 9):
        cls = uniq[bisect_left(lens, n):bisect_left(lens, n + 1)]
        hl = list(map(list, map(map, repeat(hash), cls)))
        sums = list(map(sum, hl))
        if clash:
            # two smaller sets share a hash sum: look the deletions up directly
            for a in cls:
                for x in a:
                    gb = gget(a - {x})
                    if gb is not None:
                        for i in gb:
                            for j in gget(a):
                                add((i, j) if i < j else (j, i))
        elif prev:
            dels = list(map(sub, chain.from_iterable(map(repeat, sums, repeat(n))),
                            chain.from_iterable(hl)))
            found = list(map(prev.get, dels))
            for p, b in zip(compress(count(), found), filter(None, found)):
                a = cls[p // n]
                if b < a:
                    for i in gget(b):
                        for j in gget(a):
                            add((i, j) if i < j else (j, i))
        prev = dict(zip(sums, cls))
        clash = len(prev) < len(cls)
    lo = bisect_left(lens, 8)
    if lo == len(uniq):
        return pairs
    top = lens[-1] + 1
    probe = [n - (4 * n + 4) // 5 + 1 for n in range(top)]
    keep = [n - (8 * n + 8) // 9 + 1 for n in range(top)]
    first = [bisect_left(lens, (4 * n + 4) // 5) for n in range(top)]
    freq = {}
    fget = freq.get
    for t in chain.from_iterable(uniq[lo:]):
        freq[t] = fget(t, 0) + 1
    rget = dict(zip(sorted(freq, key=fget), range(len(freq)))).get
    index = {}
    get = index.get
    for k in range(lo, bisect_left(lens, 9)):
        t = min(uniq[k], key=rget)
        kl = get(t)
        if kl is None:
            index[t] = [k]
        else:
            kl.append(k)
    for k in range(bisect_left(lens, 9), len(uniq)):
        a = uniq[k]
        n = lens[k]
        km = first[n]
        toks = sorted(a, key=rget)
        cands = set()
        for t in toks[:probe[n]]:
            kl = get(t)
            if kl:
                if kl[0] >= km:
                    cands.update(kl)
                else:
                    cands.update(kl[bisect_left(kl, km):])
        for t in toks[:keep[n]]:
            kl = get(t)
            if kl is None:
                index[t] = [k]
            else:
                kl.append(k)
        if cands:
            ga = groups[a]
            for c in cands:
                b = uniq[c]
                inter = len(a & b)
                if 5 * inter >= 4 * (n + lens[c] - inter):
                    for i in groups[b]:
                        for j in ga:
                            add((i, j) if i < j else (j, i))
    return pairs
