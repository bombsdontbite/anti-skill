from collections import Counter, defaultdict
from itertools import chain, count, groupby, repeat
from operator import sub


def near_duplicates(records):
    sets = list(map(frozenset, map(str.split, records)))
    lens = list(map(len, sets))
    pairs = []
    add = pairs.append
    order = sorted(range(len(sets)), key=lens.__getitem__)
    big = []
    eights = ()
    sigs = {}
    sget = sigs.get
    for a, grp in groupby(order, lens.__getitem__):
        if not a:
            continue
        if a < 4:
            groups = {}
            for i in grp:
                g = groups.get(sets[i])
                if g is None:
                    groups[sets[i]] = [i]
                else:
                    for c in g:
                        add((c, i))
                    g.append(i)
            continue
        if a > 8:
            big.append((a, list(grp)))
            continue
        b0 = a - 1
        if a == 8:
            grp = eights = list(grp)
        for i in grp:
            s = sets[i]
            if a > 4:
                hs = list(map(hash, s))
                S = sum(hs)
                for h in hs:
                    g = sget(S - h)
                    if g is None:
                        continue
                    for c in g:
                        if lens[c] == b0 and sets[c] < s:
                            add((c, i) if c < i else (i, c))
            else:
                S = sum(map(hash, s))
            g = sget(S)
            if g is None:
                sigs[S] = [i]
            else:
                for c in g:
                    if s == sets[c]:
                        add((c, i))
                g.append(i)
    if not big:
        return pairs
    freq = Counter(chain.from_iterable(map(sets.__getitem__, chain.from_iterable([g[::4] for _, g in big]))))
    rk = defaultdict(count().__next__, zip(sorted(freq, key=freq.__getitem__), count(1 << 40))).__getitem__
    index = {}
    iget = index.get
    for c in eights:
        t = min(sets[c], key=rk)
        lst = iget(t)
        if lst is None:
            index[t] = [(c, 7)]
        else:
            lst.append((c, 7))
    for a, grp in big:
        minb = (4 * a + 4) // 5
        p = a - minb + 1
        q = a - (8 * a + 8) // 9 + 1
        ab = 4 * a
        for i in grp:
            s = sets[i]
            seen = set()
            sadd = seen.add
            k = 0
            r = a - 1
            for t in sorted(s, key=rk)[:p]:
                lst = iget(t)
                if lst:
                    for c, rest in lst:
                        if c not in seen:
                            sadd(c)
                            b = lens[c]
                            if b >= minb and 9 * (1 + (r if r < rest else rest)) >= ab + 4 * b and 9 * len(s & sets[c]) >= ab + 4 * b:
                                add((c, i) if c < i else (i, c))
                    if k < q:
                        lst.append((i, r))
                elif k < q:
                    index[t] = [(i, r)]
                k += 1
                r -= 1
    return pairs
