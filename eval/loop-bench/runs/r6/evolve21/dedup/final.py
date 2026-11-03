from itertools import compress, repeat, combinations, chain, count, product

K = 8  # sizes <= K: a pair is identical sets or one set minus one token; sizes > K use the prefix filter


def near_duplicates(records):
    fs = list(map(frozenset, map(str.split, records)))
    last = dict(zip(fs, count()))  # distinct set -> its last record index
    last.pop(frozenset(), None)
    pairs = []
    dup = {}  # last index -> all record indices with that set, only for repeated sets
    rep = list(map(last.get, fs))
    extra = [i for i, r in enumerate(rep) if r != i]
    if extra:
        for i in extra:
            r = rep[i]
            if r is not None:
                l = dup.get(r)
                if l is None:
                    dup[r] = [i, r]
                else:
                    l.insert(-1, i)
        for l in dup.values():
            pairs.extend(combinations(l, 2))
    dg = dup.get

    def emit(i, j):
        mi = dg(i)
        mj = dg(j)
        if mi is None and mj is None:
            pairs.append((i, j) if i < j else (j, i))
        else:
            for x, y in product(mi or (i,), mj or (j,)):
                pairs.append((x, y) if x < y else (y, x))

    lk = last.keys()
    lg = last.get
    big = []
    for x in lk:
        a = len(x)
        if a > K:
            big.append(x)
        elif a >= 5:
            ks = list(map(x.difference, zip(x)))
            if not lk.isdisjoint(ks):
                i = lg(x)
                for k in ks:
                    j = lg(k)
                    if j is not None:
                        emit(i, j)
    if not big:
        return pairs
    # prefix filter over sizes >= K + 1, with size-K sets indexed as partners
    S = big + [x for x in lk if len(x) == K]
    order = sorted(zip(map(len, S), count()))
    n = len(order)
    sizes = [x[0] for x in order]
    S = [S[x[1]] for x in order]
    ids = list(map(lg, S))
    top = sizes[-1]
    firstge = [n] * (top + 2)
    for p in range(n - 1, -1, -1):
        firstge[sizes[p]] = p
    for b in range(top, -1, -1):
        if firstge[b] > firstge[b + 1]:
            firstge[b] = firstge[b + 1]
    B4 = [4 * b for b in sizes]
    freq = {}
    fg = freq.get
    for t in chain.from_iterable(S):
        freq[t] = fg(t, 0) + 1
    rk = dict(zip(sorted(freq, key=fg), count())).get
    index = {}
    ig = index.get
    for pos in range(n):
        a = sizes[pos]
        toks = sorted(map(rk, S[pos]))
        if a > K:
            s = S[pos]
            minb = (4 * a + 4) // 5
            lo = firstge[minb]
            if a < 24:
                cands = set()
                for t in toks[:a - minb + 1]:
                    lst = ig(t)
                    if lst:
                        if lst[0] < lo:
                            k = 1
                            while k < len(lst) and lst[k] < lo:
                                k += 1
                            del lst[:k]
                        cands.update(lst)
            else:
                L = []
                for t in toks[:a - minb + 2]:
                    lst = ig(t)
                    if lst:
                        if lst[0] < lo:
                            k = 1
                            while k < len(lst) and lst[k] < lo:
                                k += 1
                            del lst[:k]
                        L += lst
                L.sort()
                cands = {x for x, y in zip(L, L[1:]) if x == y}
            if cands:
                cl = list(cands)
                if len(cl) == 1:
                    good = cl if 9 * len(s & S[cl[0]]) >= 4 * a + B4[cl[0]] else ()
                else:
                    a4 = 4 * a
                    good = [c for c in cl if 9 * len(s & S[c]) >= a4 + B4[c]]
                i = ids[pos]
                for c in good:
                    emit(i, ids[c])
        for t in toks[:a - (8 * a + 8) // 9 + (2 if a >= 20 else 1)]:
            lst = ig(t)
            if lst is None:
                index[t] = [pos]
            else:
                lst.append(pos)
    return pairs
