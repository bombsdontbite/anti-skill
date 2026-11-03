STEP = 4
MINC = 2


def near_duplicates(records):
    every = list(map(frozenset, map(str.split, records)))
    n = len(every)
    # 1 + the last position of each set, so that every value is true
    last = dict(zip(every, range(1, n + 1)))
    last.pop(frozenset(), None)
    pairs = []
    groups = {}
    if len(last) < n:
        for i in sorted(set(range(1, n + 1)).difference(last.values())):
            i -= 1
            s = every[i]
            if s:
                g = groups.get(s)
                if g is None:
                    groups[s] = [i]
                else:
                    g.append(i)
        for s, g in groups.items():
            g.append(last[s] - 1)
            for x in range(len(g)):
                gx = g[x]
                for y in g[x + 1:]:
                    pairs.append((gx, y))
    sets = sorted(last, key=len)
    sizes = list(map(len, sets))
    n = len(sets)
    if not n or sizes[-1] < 5:
        return pairs
    # start[b]: first id whose set has at least b tokens
    top = max(sizes[-1], 9)
    start = [n] * (top + 2)
    k = 0
    for b in sorted(set(sizes)):
        start[b] = k = sizes.index(b, k)
    for b in range(top, -1, -1):
        if start[b] > start[b + 1]:
            start[b] = start[b + 1]
    # Below 9 tokens a partner must be the set less one token.
    gget = groups.get
    small = sets[start[4]:start[9]]
    sigs = [sum(map(hash, s)) for s in small]
    bysig = dict(zip(sigs, small))
    if len(bysig) == len(small):
        # The set less token t has signature S - hash(t); a match is checked exactly.
        sig = bysig.get
        for s, S in zip(small[start[5] - start[4]:], sigs[start[5] - start[4]:]):
            for h in map(hash, s):
                sy = sig(S - h)
                if sy is not None and sy < s and len(sy) == len(s) - 1:
                    for i in gget(s) or (last[s] - 1,):
                        for j in gget(sy) or (last[sy] - 1,):
                            pairs.append((i, j) if i < j else (j, i))
    else:
        keys = set(sets)
        for s in sets[start[5]:start[9]]:
            for sy in keys.intersection(map(s.difference, zip(s))):
                for i in gget(s) or (last[s] - 1,):
                    for j in gget(sy) or (last[sy] - 1,):
                        pairs.append((i, j) if i < j else (j, i))
    if start[9] == n:
        return pairs
    # Tokens frequent in a sample come last, by count; the rest first, by hash.
    big = sets[start[8]:]
    seen = {}
    sget = seen.get
    for s in big[::STEP]:
        for t in s:
            seen[t] = sget(t, 0) + 1
    order = sorted([t for t in seen if seen[t] >= MINC], key=sget)
    common = frozenset(order)
    key = dict(zip(order, range(len(order)))).get
    index = {}
    get = index.get
    for x in range(start[8], start[9]):
        s = sets[x]
        r = s - common
        t = min(r, key=hash) if r else min(s, key=key)
        lst = get(t)
        if lst is None:
            index[t] = [x]
        else:
            lst.append(x)
    x = start[9]
    while x < n:
        a = sizes[x]
        end = start[a + 1]
        lo = (4 * a + 4) // 5
        p = a - lo + 1
        q = a - (8 * a + 8) // 9 + 1
        a4 = 4 * a
        first = start[lo]
        bounds = []
        for i in range(p):
            bm = (5 * a - 9 * i) // 4
            if bm >= a:
                bm = a
            bounds.append((start[bm + 1], i < q))
        for x in range(x, end):
            s = sets[x]
            cands = set()
            toks = sorted(s - common, key=hash)
            if len(toks) < p:
                toks += sorted(s & common, key=key)
            for t, (hi, ins) in zip(toks, bounds):
                lst = get(t)
                if not lst:
                    if ins:
                        if lst is None:
                            index[t] = [x]
                        else:
                            lst.append(x)
                    continue
                if lst[0] < first:
                    k = 1
                    m = len(lst)
                    while k < m and lst[k] < first:
                        k += 1
                    del lst[:k]
                if lst:
                    if lst[-1] < hi:
                        cands.update(lst)
                    elif lst[0] < hi:
                        k = len(lst) - 1
                        while lst[k] >= hi:
                            k -= 1
                        cands.update(lst[:k + 1])
                if ins:
                    lst.append(x)
            for y in cands:
                sy = sets[y]
                if 9 * len(s & sy) >= a4 + 4 * sizes[y]:
                    for i in gget(s) or (last[s] - 1,):
                        for j in gget(sy) or (last[sy] - 1,):
                            pairs.append((i, j) if i < j else (j, i))
        x = end
    return pairs
