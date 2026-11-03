def near_duplicates(records):
    groups = {}
    for i, s in enumerate(map(frozenset, map(str.split, records))):
        if s:
            g = groups.get(s)
            if g is None:
                groups[s] = [i]
            else:
                g.append(i)
    pairs = []
    for g in groups.values():
        if len(g) > 1:
            for x in range(len(g)):
                gx = g[x]
                for y in range(x + 1, len(g)):
                    pairs.append((gx, g[y]))
    # Up to 8 tokens a set only matches an identical one or itself minus one token (from 4 up).
    found = []
    for s in groups:
        n = len(s)
        if 4 < n < 9:
            for t in s:
                d = s.difference((t,))
                if d in groups:
                    found.append((d, s))
    keys = sorted([s for s in groups if len(s) > 7], key=len)
    if not keys:
        return emit(pairs, found, groups)
    freq = {}
    fget = freq.get
    for s in keys:
        for t in s:
            freq[t] = fget(t, 0) + 1
    order = sorted(freq, key=fget)
    rank = dict(zip(order, range(len(order)))).get
    top = len(keys[-1])
    start = [len(keys)] * (top + 2)
    for k in range(len(keys) - 1, -1, -1):
        start[len(keys[k])] = k
    for n in range(top, -1, -1):
        if start[n] > start[n + 1]:
            start[n] = start[n + 1]
    index = {}
    get = index.get
    cands = []
    for k, s in enumerate(keys):
        n = len(s)
        lo = (4 * n + 4) // 5
        p = n - lo + 1
        klo = start[lo]
        khi = start[n] if n < 9 else k
        if p == 1:
            t = min(s, key=rank)
            lst = get(t)
            if lst is None:
                index[t] = [k]
            else:
                if lst[-1] >= klo:
                    if lst[0] < klo:
                        j = 1
                        while lst[j] < klo:
                            j += 1
                        index[t] = lst = lst[j:]
                    if lst[-1] < khi:
                        cands.extend([(c, k) for c in lst])
                    else:
                        cands.extend([(c, k) for c in lst if c < khi])
                lst.append(k)
        else:
            toks = sorted(s, key=rank)
            for t in toks[:p] if n > 8 else ():
                lst = get(t)
                if lst is not None and lst[-1] >= klo:
                    if lst[0] < klo:
                        j = 1
                        while lst[j] < klo:
                            j += 1
                        index[t] = lst = lst[j:]
                    if lst[-1] < khi:
                        cands.extend([(c, k) for c in lst])
                    else:
                        cands.extend([(c, k) for c in lst if c < khi])
            for t in toks[:n - (8 * n + 8) // 9 + 1]:
                lst = get(t)
                if lst is None:
                    index[t] = [k]
                else:
                    lst.append(k)
    for x, y in set(cands):
        a = keys[x]
        b = keys[y]
        if 9 * len(a & b) >= 4 * (len(a) + len(b)):
            found.append((a, b))
    return emit(pairs, found, groups)


def emit(pairs, found, groups):
    for a, b in found:
        for i in groups[a]:
            for j in groups[b]:
                pairs.append((i, j) if i < j else (j, i))
    return pairs
