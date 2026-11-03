from collections import Counter


def near_duplicates(records):
    sets = [frozenset(r.split()) for r in records]
    freq = Counter()
    for s in sets:
        freq.update(s)
    rank = {t: k for k, t in enumerate(sorted(freq, key=lambda t: (freq[t], t)))}
    rget = rank.get
    order = sorted((i for i in range(len(sets)) if sets[i]), key=lambda i: len(sets[i]))
    index = {}
    pairs = []
    append = pairs.append
    for i in order:
        s = sets[i]
        a = len(s)
        toks = sorted(map(rget, s))
        need = (4 * a + 4) // 5
        cands = set()
        for t in toks[:a - need + 1]:
            lst = index.get(t)
            if lst:
                cands.update(lst)
        for j in cands:
            b = sets[j]
            lb = len(b)
            if lb < need:
                continue
            inter = len(s & b)
            if 5 * inter >= 4 * (a + lb - inter):
                append((j, i) if j < i else (i, j))
        for t in toks[:a - (8 * a + 8) // 9 + 1]:
            lst = index.get(t)
            if lst is None:
                index[t] = [i]
            else:
                lst.append(i)
    return pairs
