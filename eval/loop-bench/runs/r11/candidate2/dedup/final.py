from itertools import chain, repeat, count


def near_duplicates(records):
    toks = list(map(str.split, records))
    # token -> int id, raised by its frequency in a sample; any total order is correct
    key = dict(zip(set(chain.from_iterable(toks)), count()))
    nd = len(key)
    for t in chain.from_iterable(toks[::STEP]):
        key[t] += nd
    groups = {}
    for i, s in enumerate(map(frozenset, map(map, repeat(key.get), toks))):
        if s:
            g = groups.get(s)
            if g is None:
                groups[s] = [i]
            else:
                g.append(i)
    pairs = []
    bysize = {}
    for s, g in groups.items():
        if len(g) > 1:
            for a in range(len(g)):
                ga = g[a]
                for b in g[a + 1:]:
                    pairs.append((ga, b))
        n = len(s)
        # distinct sets of 3 or fewer tokens can never reach 0.8
        if n > 3:
            b = bysize.get(n)
            if b is None:
                bysize[n] = [s]
            else:
                b.append(s)
    if not bysize:
        return pairs
    sizes = sorted(bysize)
    uniq = []
    for n in sizes:
        uniq += bysize[n]
    index = {}
    ig = index.get
    x = 0
    for n in sizes:
        bucket = bysize[n]
        minlen = (4 * n + 4) // 5
        pp = n - (4 * (n + minlen) + 8) // 9 + 1
        pi = n - (8 * n + 8) // 9 + 1
        # overlap needed against each smaller-or-equal size
        need_n = [(4 * (n + m) + 8) // 9 for m in range(n + 1)]
        for s, ks in zip(bucket, map(sorted, bucket)):
            cands = set()
            for t in ks[:pp]:
                lst = ig(t)
                if lst is not None:
                    cands.update(lst)
            for t in ks[:pi]:
                lst = ig(t)
                if lst is None:
                    index[t] = [x]
                else:
                    lst.append(x)
            x += 1
            for y in cands:
                o = uniq[y]
                lo = len(o)
                if lo < minlen:
                    continue
                need = need_n[lo]
                if need > lo:
                    continue
                if need == lo:
                    ok = o <= s
                else:
                    ok = len(s & o) >= need
                if ok:
                    for i in groups[s]:
                        for j in groups[o]:
                            pairs.append((i, j) if i < j else (j, i))
    return pairs


STEP = 5
