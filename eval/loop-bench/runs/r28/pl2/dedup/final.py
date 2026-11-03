def near_duplicates(records):
    sets = [frozenset(r.split()) for r in records]
    freq = {}
    for s in sets:
        for t in s:
            freq[t] = freq.get(t, 0) + 1
    rank = {t: k for k, t in enumerate(sorted(freq, key=lambda t: (freq[t], t)))}
    order = sorted((i for i in range(len(sets)) if sets[i]), key=lambda i: len(sets[i]))
    index = {}
    pairs = []
    append = pairs.append
    lens = [len(s) for s in sets]
    for i in order:
        a = sets[i]
        n = lens[i]
        toks = sorted(a, key=rank.get)
        minlen = (4 * n + 4) // 5
        probe = n - minlen + 1
        cands = set()
        for t in toks[:probe]:
            lst = index.get(t)
            if lst is not None:
                cands.update(lst)
        for j in cands:
            m = lens[j]
            if m >= minlen:
                inter = len(a & sets[j])
                if 5 * inter >= 4 * (n + m - inter):
                    append((i, j) if i < j else (j, i))
        ip = n - (8 * n + 8) // 9 + 1
        for t in toks[:ip]:
            lst = index.get(t)
            if lst is None:
                index[t] = [i]
            else:
                lst.append(i)
    return pairs
