def near_duplicates(records):
    sets = [set(r.split()) for r in records]
    freq = {}
    for s in sets:
        for t in s:
            freq[t] = freq.get(t, 0) + 1
    rank = {t: (c, t) for t, c in freq.items()}
    key = rank.__getitem__
    order = sorted((i for i in range(len(sets)) if sets[i]), key=lambda i: len(sets[i]))
    index = {}
    pairs = []
    for x in order:
        a = sets[x]
        n = len(a)
        lo = (4 * n + 4) // 5
        p = n - lo + 1
        prefix = sorted(a, key=key)[:p] if p < n else a
        seen = set()
        for t in prefix:
            lst = index.get(t)
            if lst is None:
                index[t] = [x]
                continue
            for y in lst:
                if y in seen:
                    continue
                seen.add(y)
                b = sets[y]
                m = len(b)
                if m >= lo and 9 * len(a & b) >= 4 * (n + m):
                    pairs.append((y, x) if y < x else (x, y))
            lst.append(x)
    return pairs
