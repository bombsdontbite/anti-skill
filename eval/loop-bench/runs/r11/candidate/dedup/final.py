from itertools import chain, combinations, groupby


def near_duplicates(records):
    n = len(records)
    fs = list(map(frozenset, map(str.split, records)))
    first = dict(zip(fs[::-1], range(n - 1, -1, -1)))
    first.pop(frozenset(), None)
    pairs = []
    mem = {}
    for i, r in enumerate(map(first.get, fs)):
        if r is not None and r != i:
            if r in mem:
                mem[r].append(i)
            else:
                mem[r] = [r, i]
    for g in mem.values():
        pairs += combinations(g, 2)
    hits = []
    small = sorted([s for s in first if 3 < len(s) < 9], key=len)
    D = {}
    isd = D.keys().isdisjoint
    coll = {}
    for s in small:
        hs = list(map(hash, s))
        H = sum(hs)
        if len(s) > 4 and not isd([H - h for h in hs]):
            found = set()
            for h in hs:
                if H - h in D:
                    found.update(coll.get(H - h, (D[H - h],)))
            hits += [(s, o) for o in found if len(o) + 1 == len(s) and o < s]
        if D.setdefault(H, s) is not s:
            coll.setdefault(H, [D[H]]).append(s)
    big = sorted([s for s in first if len(s) > 7], key=len)
    rk = dict(zip(chain.from_iterable(big), range(1 << 62))).get
    index = {}
    ig = index.get
    for a, grp in groupby(big, len):
        P = a - (4 * a + 4) // 5 + 2
        Q = a - (8 * a + 8) // 9 + 2
        a4 = 4 * a
        for s in grp:
            toks = sorted(map(rk, s))
            cands = set(chain.from_iterable(filter(None, map(ig, combinations(toks[:P], 2)))))
            for k in combinations(toks[:Q], 2):
                if k in index:
                    index[k].append(s)
                else:
                    index[k] = [s]
            if cands:
                hits += [(s, o) for o in cands if 5 * len(o) >= a4 and 9 * len(s & o) >= a4 + 4 * len(o)]
    for s, o in hits:
        for i in mem.get(first[o]) or (first[o],):
            for j in mem.get(first[s]) or (first[s],):
                pairs.append((i, j) if i < j else (j, i))
    return pairs
