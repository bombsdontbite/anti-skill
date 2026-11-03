from itertools import chain


def near_duplicates(records):
    sets = list(map(frozenset, map(str.split, records)))
    empty = frozenset()
    pos = dict(zip(sets, range(len(sets))))
    pos.pop(empty, None)
    pairs = []
    if len(pos) == len(sets) - sets.count(empty):
        groups = None
        known = pos
    else:
        groups = {}
        for i, s in enumerate(sets):
            g = groups.get(s)
            if g is None:
                groups[s] = [i]
            else:
                g.append(i)
        groups.pop(empty, None)
        known = groups
        for g in groups.values():
            if len(g) > 1:
                n = len(g)
                for a in range(n - 1):
                    ia = g[a]
                    for b in range(a + 1, n):
                        pairs.append((ia, g[b]))
    # With |A & B| = i and d + e tokens on either side only, 5i >= 4(i + d + e) means
    # d + e <= i / 4: distinct sets pair only if i >= 4, and while the larger set has
    # at most 8 tokens its partner is that set minus one token.
    hits = []
    big = []
    probes = []
    sig = {}
    for s in known:
        n = len(s)
        if n < 4:
            continue
        if n < 9:
            h = sum(map(hash, s))
            if n < 8:
                sig[h] = s
            if n > 4:
                probes.append((s, h))
            if n < 8:
                continue
        big.append(s)
    if len(sig) == sum(4 <= len(s) < 8 for s in known):
        get = sig.get
        for s, h in probes:
            m = len(s) - 1
            for x in map(hash, s):
                o = get(h - x)
                if o is not None and len(o) == m and o < s:
                    hits.append((s, o))
    else:
        for s, h in probes:
            for o in map(s.difference, zip(s)):
                if o in known:
                    hits.append((s, o))
    if big:
        big.sort(key=len)
        seen = list(dict.fromkeys(chain.from_iterable(big)))
        key = dict(zip(seen, range(len(seen), 0, -1))).__getitem__
        index = [None] * (len(seen) + 1)
        for k, s in enumerate(big):
            n = len(s)
            order = sorted(map(key, s))
            if n > 8:
                lo4 = (4 * n + 4) // 5
                cand = set()
                for t in order[:n - lo4 + 1]:
                    c = index[t]
                    if c:
                        cand.update(c)
                for c in cand:
                    o = big[c]
                    lo = len(o)
                    if lo < lo4:
                        continue
                    inter = len(s & o)
                    if 5 * inter >= 4 * (n + lo - inter):
                        hits.append((s, o))
            for t in order[:n - (8 * n + 8) // 9 + 1]:
                c = index[t]
                if c is None:
                    index[t] = [k]
                else:
                    c.append(k)
    if groups is None:
        for s, o in hits:
            a = pos[s]
            b = pos[o]
            pairs.append((a, b) if a < b else (b, a))
    else:
        for s, o in hits:
            for a in groups[s]:
                for b in groups[o]:
                    pairs.append((a, b) if a < b else (b, a))
    return pairs
