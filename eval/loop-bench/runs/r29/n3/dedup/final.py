from collections import Counter
from itertools import chain, combinations, repeat
from operator import sub


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
    big = []
    small = []
    for b, gy in groups.items():
        if len(gy) > 1:
            pairs.extend(combinations(gy, 2))
        lb = len(b)
        if lb >= 4:
            if lb < 9:
                small.append(b)
            if lb >= 8:
                big.append(b)
    if small:
        hs = list(map(sum, map(map, repeat(hash), small)))
        sig = {}
        sget = sig.get
        for b, h in zip(small, hs):
            if len(b) < 8:
                lst = sget(h)
                if lst is None:
                    sig[h] = [b]
                else:
                    lst.append(b)
        for b, h in zip(small, hs):
            lb = len(b)
            if lb > 4:
                for lst in filter(None, map(sget, map(sub, repeat(h), map(hash, b)))):
                    for a in lst:
                        if len(a) == lb - 1 and a < b:
                            gy = groups[b]
                            for p in groups[a]:
                                for q in gy:
                                    pairs.append((p, q) if p < q else (q, p))
    if not big:
        return pairs
    big.sort(key=len)
    cnt = Counter(chain.from_iterable(big))
    m = len(cnt)
    rank = {t: f * m + k for k, (t, f) in enumerate(cnt.items())}
    rget = rank.get
    m2 = 2 * m
    index = {}
    iget = index.get
    for y, b in enumerate(big):
        lb = len(b)
        toks = sorted(map(rget, b))
        if lb > 8:
            mo = (4 * lb + 4) // 5
            p = lb - mo + 1
            if toks[p - 1] < m2:
                continue
            cands = set()
            for t in toks[:p]:
                lst = iget(t)
                if lst:
                    cands.update(lst)
            if cands:
                gy = groups[b]
                need = 4 * lb
                for x in cands:
                    a = big[x]
                    la = len(a)
                    if la >= mo and 9 * len(a & b) >= need + 4 * la:
                        for q in gy:
                            for pp in groups[a]:
                                pairs.append((pp, q) if pp < q else (q, pp))
        for t in toks[:lb - (8 * lb + 8) // 9 + 1]:
            if t >= m2:
                lst = iget(t)
                if lst is None:
                    index[t] = [y]
                else:
                    lst.append(y)
    return pairs
