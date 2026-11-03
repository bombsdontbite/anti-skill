from collections import Counter
from itertools import chain


def near_duplicates(records):
    groups = {}
    for i, s in enumerate(map(frozenset, map(str.split, records))):
        if s in groups:
            groups[s].append(i)
        else:
            groups[s] = [i]
    groups.pop(frozenset(), None)
    pairs = []
    if len(groups) < len(records):
        for ids in groups.values():
            if len(ids) > 1:
                for a in range(len(ids)):
                    x = ids[a]
                    for y in ids[a + 1:]:
                        pairs.append((x, y))
    if len(groups) < 2:
        return pairs
    freq = Counter(chain.from_iterable(groups))
    rank = {t: k for k, t in enumerate(sorted(freq, key=freq.__getitem__))}
    rget = rank.__getitem__
    index = {}
    iget = index.get
    found = []
    for s in sorted(groups, key=len):
        n = len(s)
        minlen = (4 * n + 4) // 5
        toks = sorted(s, key=rget)
        counts = None
        for i in range(n - minlen + 1):
            lst = iget(toks[i])
            if lst is None:
                continue
            if counts is None:
                counts = {}
                cget = counts.get
            rest = n - i
            for y, j, m in lst:
                if m < minlen:
                    continue
                c = cget(y, 0)
                if c < 0:
                    continue
                r2 = m - j
                if c + (rest if rest < r2 else r2) >= (4 * (n + m) + 8) // 9:
                    counts[y] = c + 1
                else:
                    counts[y] = -1
        for i in range(n - (8 * n + 8) // 9 + 1):
            t = toks[i]
            lst = iget(t)
            if lst is None:
                index[t] = [(s, i, n)]
            else:
                lst.append((s, i, n))
        if counts:
            for y, c in counts.items():
                if c > 0:
                    inter = len(s & y)
                    if 5 * inter >= 4 * (n + len(y) - inter):
                        found.append((s, y))
    for s, y in found:
        ix = groups[s]
        for q in groups[y]:
            for a in ix:
                pairs.append((a, q) if a < q else (q, a))
    return pairs
