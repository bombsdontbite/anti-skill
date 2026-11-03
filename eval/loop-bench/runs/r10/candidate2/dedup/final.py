def near_duplicates(records):
    groups = {}
    for i, r in enumerate(records):
        s = frozenset(r.split())
        g = groups.get(s)
        if g is None:
            groups[s] = [i]
        else:
            g.append(i)
    groups.pop(frozenset(), None)
    pairs = []
    append = pairs.append
    for g in groups.values():
        if len(g) > 1:
            for x in range(len(g)):
                gi = g[x]
                for y in range(x + 1, len(g)):
                    append((gi, g[y]))
    # distinct sets of at most 3 tokens are never 80 % alike
    sets = [s for s in groups if len(s) > 3]
    members = [groups[s] for s in sets]
    freq = {}
    fget = freq.get
    for s in sets:
        for t in s:
            freq[t] = fget(t, 0) + 1
    rank = {t: k for k, t in enumerate(sorted(freq, key=freq.get))}
    order = sorted(range(len(sets)), key=lambda i: len(sets[i]))
    rget = rank.get
    index = {}
    start = {}
    # on dense inputs the filters stop pruning; then compare pairwise like the reference
    work = 0
    limit = len(sets) ** 2 // 20 + 10000
    for r, i in enumerate(order):
        if work > limit:
            break
        sa = sets[i]
        n = len(sa)
        lo4 = 4 * n
        p = n - (lo4 + 4) // 5 + 1
        if n == 4:
            t = min(sa, key=rget)
            lst = index.get(t)
            if lst is None:
                index[t] = [(i, n, 0)]
                start[t] = 0
            else:
                lst.append((i, n, 0))
            continue
        if p == 1:
            t = min(sa, key=rget)
            lst = index.get(t)
            if lst is None:
                index[t] = [(i, n, 0)]
                start[t] = 0
                continue
            k = start[t]
            if 5 * lst[k][1] < lo4:
                L = len(lst)
                k += 1
                while k < L and 5 * lst[k][1] < lo4:
                    k += 1
                start[t] = k
            hits = [e[0] for e in lst[k:]]
            lst.append((i, n, 0))
        else:
            a = sorted(sa, key=rget)
            cnt = {}
            for pos in range(p):
                t = a[pos]
                lst = index.get(t)
                if lst is None:
                    index[t] = [(i, n, pos)]
                    start[t] = 0
                    continue
                k = start[t]
                if 5 * lst[k][1] < lo4:
                    L = len(lst)
                    k += 1
                    while k < L and 5 * lst[k][1] < lo4:
                        k += 1
                    start[t] = k
                rest = n - pos - 1
                work += len(lst) - k
                for j, m, q in lst[k:] if k else lst:
                    c = cnt.get(j, 0)
                    if c < 0:
                        continue
                    if c + 1 + min(rest, m - q - 1) < (4 * (n + m) + 8) // 9:
                        cnt[j] = -1
                    else:
                        cnt[j] = c + 1
                lst.append((i, n, pos))
            hits = [j for j, c in cnt.items() if c > 0]
        for j in hits:
            b = sets[j]
            inter = len(sa & b)
            if 5 * inter >= 4 * (n + len(b) - inter):
                for x in members[i]:
                    for y in members[j]:
                        append((x, y) if x < y else (y, x))
    else:
        return pairs
    lo = 0
    for r in range(r, len(order)):
        i = order[r]
        sa = sets[i]
        n = len(sa)
        while 5 * len(sets[order[lo]]) < 4 * n:
            lo += 1
        for j in order[lo:r]:
            b = sets[j]
            inter = len(sa & b)
            if 5 * inter >= 4 * (n + len(b) - inter):
                for x in members[i]:
                    for y in members[j]:
                        append((x, y) if x < y else (y, x))
    return pairs
