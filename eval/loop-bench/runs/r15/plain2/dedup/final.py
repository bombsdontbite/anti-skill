from collections import defaultdict


def near_duplicates(records):
    groups = {}
    for i, r in enumerate(records):
        s = frozenset(r.split())
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

    sets = list(groups)
    if len(sets) < 2:
        return pairs
    freq = defaultdict(int)
    for s in sets:
        for t in s:
            freq[t] += 1
    rank = {t: k for k, t in enumerate(sorted(freq, key=lambda t: (freq[t], t)))}

    order = sorted(range(len(sets)), key=lambda k: len(sets[k]))
    members = [groups[sets[k]] for k in order]
    toks = [sorted(sets[k], key=rank.get) for k in order]
    isets = [sets[k] for k in order]
    sizes = [len(t) for t in toks]

    index = defaultdict(list)
    for x in range(len(toks)):
        tx = toks[x]
        n = sizes[x]
        minsz = (4 * n + 4) // 5
        p = n - minsz + 1
        ax = isets[x]
        cands = set()
        for i in range(p):
            lst = index.get(tx[i])
            if lst:
                for y in lst:
                    if sizes[y] >= minsz:
                        cands.add(y)
        for y in cands:
            inter = len(ax & isets[y])
            if 5 * inter >= 4 * (n + sizes[y] - inter):
                for a in members[x]:
                    for b in members[y]:
                        pairs.append((a, b) if a < b else (b, a))
        for i in range(p):
            index[tx[i]].append(x)
    return pairs
