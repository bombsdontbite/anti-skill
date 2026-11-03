def near_duplicates(records):
    sets = [set(r.split()) for r in records]
    freq = {}
    for s in sets:
        for w in s:
            freq[w] = freq.get(w, 0) + 1
    rank = {w: k for k, w in enumerate(sorted(freq, key=lambda w: (freq[w], w)))}
    items = sorted((len(s), i) for i, s in enumerate(sets) if s)
    size = [len(s) for s in sets]
    index = {}
    pairs = []
    append = pairs.append
    for n, i in items:
        a = sets[i]
        minsize = (4 * n + 4) // 5
        prefix = sorted([rank[w] for w in a])[:n - minsize + 1]
        cands = set()
        for t in prefix:
            lst = index.get(t)
            if lst is None:
                index[t] = [i]
            else:
                cands.update(lst)
                lst.append(i)
        for j in cands:
            m = size[j]
            if m >= minsize:
                inter = len(a & sets[j])
                if 5 * inter >= 4 * (n + m - inter):
                    append((j, i) if j < i else (i, j))
    return pairs
