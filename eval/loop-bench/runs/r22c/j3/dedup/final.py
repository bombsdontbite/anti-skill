from itertools import chain


def near_duplicates(records):
    groups = {}
    gget = groups.get
    for i, r in enumerate(records):
        s = frozenset(r.split())
        g = gget(s)
        if g is None:
            groups[s] = [i]
        else:
            g.append(i)
    groups.pop(frozenset(), None)
    pairs = []
    big = []
    mid = []
    for s, g in groups.items():
        if len(g) > 1:
            for x in range(len(g)):
                gx = g[x]
                for y in g[x + 1:]:
                    pairs.append((gx, y))
        a = len(s)
        if a > 3:
            if a < 9:
                mid.append(s)
            if a > 7:
                big.append(s)
    # Up to 8 tokens a partner is identical or one token smaller; find the
    # smaller one by the sum of token hashes, then check it exactly.
    sums = {}
    clash = set()
    for s in mid:
        if len(s) < 8:
            h = sum(map(hash, s))
            if h in sums:
                clash.add(h)
            else:
                sums[h] = s
    if sums:
        keyset = set(sums)
        for s in mid:
            a = len(s)
            if a > 4:
                hs = list(map(hash, s))
                h = sum(hs)
                found = {h - x for x in hs} & keyset
                if found:
                    if found & clash:
                        subs = [s - {t} for t in s]
                        subs = [t for t in subs if t in groups]
                    else:
                        subs = [t for t in map(sums.get, found) if len(t) == a - 1 and t < s]
                    for t in subs:
                        for i in groups[s]:
                            for j in groups[t]:
                                pairs.append((i, j) if i < j else (j, i))
    if not big:
        return pairs
    keys = sorted(big, key=len)
    # Tokens first seen late are mostly rare; order them first.
    seen = list(dict.fromkeys(chain.from_iterable(keys)))
    rank = dict(zip(seen, range(len(seen), 0, -1)))
    rget = rank.get
    index = {}
    iget = index.get
    sizes = []
    for xi, s in enumerate(keys):
        a = len(s)
        toks = sorted(map(rget, s))
        if a > 8:
            minb = (4 * a + 4) // 5
            cand = set()
            for t in toks[:a - minb + 1]:
                lst = iget(t)
                if lst:
                    cand.update(lst)
            gx = None
            for y in cand:
                b = sizes[y]
                if b < minb:
                    continue
                ys = keys[y]
                inter = len(s & ys)
                if 5 * inter >= 4 * (a + b - inter):
                    if gx is None:
                        gx = groups[s]
                    for i in gx:
                        for j in groups[ys]:
                            pairs.append((i, j) if i < j else (j, i))
        sizes.append(a)
        for t in toks[:a - (8 * a + 8) // 9 + 1]:
            lst = iget(t)
            if lst is None:
                index[t] = [xi]
            else:
                lst.append(xi)
    return pairs
