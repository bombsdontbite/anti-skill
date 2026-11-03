def near_duplicates(records):
    # Pairs with |A| + |B| <= 17 can differ by at most one token (equal, or one is the other plus
    # one), so they are joined on a sum-of-hashes key without counting or sorting; the rest go
    # through prefix filtering ordered by token frequency.
    sets = [set(r.split()) for r in records]
    pairs = []
    add = pairs.append
    exact = {}
    small = {}
    sget = small.get
    eget = exact.get
    big = []
    mid = []
    for i, s in enumerate(sets):
        n = len(s)
        if not n:
            continue
        if n <= 3:
            f = frozenset(s)
            lst = sget(f)
            if lst is None:
                small[f] = [i]
            else:
                for j in lst:
                    add((j, i))
                lst.append(i)
            continue
        if n <= 8:
            k = sum(map(hash, s))
            lst = eget(k)
            if lst is None:
                exact[k] = [i]
            else:
                for j in lst:
                    if sets[j] == s:
                        add((j, i))
                lst.append(i)
            if n >= 5:
                mid.append((i, k))
            if n == 8:
                big.append((n, i))
        else:
            if n == 9:
                mid.append((i, sum(map(hash, s))))
            big.append((n, i))
    for i, k in mid:
        s = sets[i]
        m = len(s) - 1
        for t in s:
            lst = eget(k - hash(t))
            if lst:
                for j in lst:
                    x = sets[j]
                    if len(x) == m and t not in x and x <= s:
                        add((j, i) if j < i else (i, j))
    if not big:
        return pairs
    freq = {}
    fg = freq.get
    for n, i in big:
        for t in sets[i]:
            freq[t] = fg(t, 0) + 1
    big.sort()
    index = {}
    iget = index.get
    sizes = [0] * len(sets)
    for n, i in big:
        s = sets[i]
        sizes[i] = n
        toks = sorted(s, key=fg)
        q = n - (8 * n + 8) // 9
        fb = fg(toks[q])
        if fb > 1:
            e2 = q + 1
            while e2 < n and fg(toks[e2]) == fb:
                e2 += 1
        else:
            e2 = 0
        cand = None
        for tok in toks[:e2]:
            lst = iget(tok)
            if lst is None:
                index[tok] = [i]
            else:
                if cand is None:
                    cand = set(lst)
                else:
                    cand.update(lst)
                lst.append(i)
        if n >= 9:
            p = n - (4 * n + 4) // 5
            fb = fg(toks[p])
            if fb > 1:
                e = p + 1
                while e < n and fg(toks[e]) == fb:
                    e += 1
                for tok in toks[e2:e]:
                    lst = iget(tok)
                    if lst:
                        if cand is None:
                            cand = set(lst)
                        else:
                            cand.update(lst)
            if cand:
                cand.discard(i)
                minlen = max((4 * n + 4) // 5, 18 - n)
                for j in cand:
                    m = sizes[j]
                    if m >= minlen:
                        inter = len(s & sets[j])
                        if 5 * inter >= 4 * (n + m - inter):
                            add((j, i) if j < i else (i, j))
    return pairs
