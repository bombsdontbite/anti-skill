from collections import Counter
from itertools import chain, repeat
from operator import sub


def near_duplicates(records):
    fs = list(map(frozenset, map(str.split, records)))
    last = dict(zip(fs, range(len(fs))))
    pairs = []
    multi = {}
    if len(last) < len(fs):
        for i in [i for i, s in enumerate(fs) if last[s] != i]:
            g = multi.get(fs[i])
            if g is None:
                multi[fs[i]] = [i]
            else:
                g.append(i)
        multi.pop(frozenset(), None)
        for s, g in multi.items():
            g.append(last[s])
            for a in range(len(g)):
                ga = g[a]
                for b in g[a + 1:]:
                    pairs.append((ga, b) if ga < b else (b, ga))
    # Distinct sets that are 80 % alike and both of at most 8 tokens are exactly
    # a set and itself plus one token, with the smaller of 4 to 7 tokens;
    # look the smaller one up by its sum of token hashes, then check it is a subset
    sums = {}
    big = []
    for s in last:
        n = len(s)
        if 3 < n < 9:
            h = sum(map(hash, s))
            if n < 8:
                g = sums.get(h)
                if g is None:
                    sums[h] = [s]
                else:
                    g.append(s)
            if n > 4:
                big.append((s, h))
    sget = sums.get
    for b, h in big:
        n = len(b) - 1
        for g in filter(None, map(sget, map(sub, repeat(h), map(hash, b)))):
            for a in g:
                if len(a) == n and a < b:
                    xs = multi.get(b) or (last[b],)
                    ys = multi.get(a) or (last[a],)
                    for x in xs:
                        for y in ys:
                            pairs.append((x, y) if x < y else (y, x))
    # every other similar pair has a set of 9 tokens or more, and both of 8 or more
    sets = sorted([s for s in last if len(s) > 7], key=len)
    freq = Counter(chain.from_iterable(sets))
    rank = {t: r for r, t in enumerate(sorted(freq, key=freq.get))}
    rget = rank.get
    index = {}
    for k, s in enumerate(sets):
        n = len(s)
        toks = sorted(s, key=rget)
        minlen = (4 * n + 4) // 5
        p = n - minlen + 1
        q = n - (8 * n + 8) // 9 + 1
        cands = set()
        for t in toks[:p]:
            lst = index.get(t)
            if lst is not None:
                cands.update(lst)
        for t in toks[:q]:
            lst = index.get(t)
            if lst is None:
                index[t] = [k]
            else:
                lst.append(k)
        for m in cands:
            b = sets[m]
            lb = len(b)
            if lb < minlen:
                continue
            inter = len(s & b)
            if 5 * inter >= 4 * (n + lb - inter):
                xs = multi.get(s) or (last[s],)
                ys = multi.get(b) or (last[b],)
                for x in xs:
                    for y in ys:
                        pairs.append((x, y) if x < y else (y, x))
    return pairs
