from collections import Counter
from itertools import chain


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
    for ids in groups.values():
        if len(ids) > 1:
            for x in range(len(ids)):
                a = ids[x]
                for b in ids[x + 1:]:
                    pairs.append((a, b))
    sets = sorted([s for s in groups if len(s) > 3], key=len)
    if len(sets) < 2:
        return pairs
    df = Counter(chain.from_iterable(sets))
    rank = {t: r for r, t in enumerate(sorted(df, key=df.get))}
    rget = rank.get
    index = {}
    iget = index.get
    lens = [len(s) for s in sets]
    for k, s in enumerate(sets):
        n = lens[k]
        minlen = (4 * n + 4) // 5
        toks = sorted(s, key=rget)
        pi = n - (8 * n + 8) // 9 + 1
        cand = set()
        j = 0
        for t in toks[:n - minlen + 1]:
            e = iget(t)
            if e is None:
                if j < pi:
                    index[t] = [0, k]
            else:
                st = e[0] + 1
                ln = len(e)
                while st < ln and lens[e[st]] < minlen:
                    st += 1
                e[0] = st - 1
                cand.update(e[st:])
                if j < pi:
                    e.append(k)
            j += 1
        if cand:
            n4 = 4 * n
            hits = [c for c in cand if 9 * len(s & sets[c]) >= n4 + 4 * lens[c]]
            if hits:
                gk = groups[s]
                for c in hits:
                    for a in gk:
                        for b in groups[sets[c]]:
                            pairs.append((a, b) if a < b else (b, a))
    return pairs
