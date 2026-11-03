from collections import Counter
from itertools import chain, combinations, count, repeat
from operator import add, mul


def near_duplicates(records):
    fs = list(map(frozenset, map(str.split, records)))
    ids = dict(zip(fs, range(len(fs))))
    out = []
    groups = None
    if len(ids) != len(fs):
        ids.pop(frozenset(), None)
        groups = {}
        for i, s in [(i, s) for i, s in enumerate(fs) if s and ids[s] != i]:
            g = groups.get(s)
            if g is None:
                groups[s] = [i]
            else:
                g.append(i)
        for s, g in groups.items():
            g.append(ids[s])
            out.extend(combinations(g, 2))
    ids.pop(frozenset(), None)
    # Distinct sets of up to 4 tokens never pair, and a 4-token set pairs only with a 5-token superset.
    sets = sorted(ids, key=len)
    lens = list(map(len, sets))
    top = lens[-1] if lens else 0
    first = [0] * (top + 2)
    size_count = Counter(lens).get
    for m in range(top + 1):
        first[m + 1] = first[m] + size_count(m, 0)
    if top > 4:
        freq = Counter(chain.from_iterable(sets[first[4]:]))
        # Rank by frequency, ties by first appearance: frequency * size + position.
        size = len(freq)
        rank = dict(zip(freq, map(add, map(mul, freq.values(), repeat(size)), count()))).get
        # Tokens in one set can never be shared; they rank first.
        nsingle = 2 * size
        index = {}
        # Up to size 8 a set pairs only with an (n - 1)-subset, so sizes 4 to 7 get their own index.
        small = [{} for _ in range(8)]
        pairs = []
        start = first[4]
        for n in range(4, top + 1):
            end = first[n + 1]
            if start == end:
                continue
            minsize = (4 * n + 4) // 5
            p0 = n - minsize + 1
            q0 = n - (8 * n + 8) // 9 + 1
            lo = first[minsize]
            # Smallest overlap a size-m set needs; when it is m the test is a subset test.
            req = [(4 * (n + m) + 8) // 9 for m in range(n + 1)]
            # Tokens before position i are not in any set first met there.
            his = []
            for i in range(p0):
                mmax = (5 * n - 9 * i) // 4
                if mmax >= n:
                    mmax = n if n > 8 else n - 1
                his.append(first[mmax + 1])
            if n <= 8:
                below = small[n - 1]
                here = small[n] if n < 8 else None
                for x in range(start, end):
                    s = sets[x]
                    toks = sorted(s, key=rank)
                    if rank(toks[p0 - 1]) < nsingle:
                        continue
                    t = toks[0]
                    if rank(t) < nsingle:
                        lst = below.get(toks[1])
                        if lst:
                            for o in filter(s.issuperset, lst):
                                pairs.append((o, s))
                        continue
                    if n > 4:
                        lst = below.get(t)
                        lst2 = below.get(toks[1])
                        if lst2:
                            if lst:
                                lst = set(lst)
                                lst.update(lst2)
                            else:
                                lst = lst2
                        if lst:
                            for o in filter(s.issuperset, lst):
                                pairs.append((o, s))
                    if here is None:
                        lst = index.get(t)
                        if lst is None:
                            index[t] = [x]
                        else:
                            lst.append(x)
                    else:
                        lst = here.get(t)
                        if lst is None:
                            here[t] = [s]
                        else:
                            lst.append(s)
                start = end
                continue
            for x in range(start, end):
                s = sets[x]
                toks = sorted(s, key=rank)
                if rank(toks[p0 - 1]) < nsingle:
                    continue
                k = 0
                while rank(toks[k]) < nsingle:
                    k += 1
                if n > 4:
                    cands = None
                    for i in range(k, p0):
                        lst = index.get(toks[i])
                        if lst:
                            if lst[0] < lo:
                                c = 1
                                while c < len(lst) and lst[c] < lo:
                                    c += 1
                                del lst[:c]
                                if not lst:
                                    continue
                            hi = his[i]
                            if lst[-1] >= hi:
                                e = len(lst) - 1
                                while e and lst[e - 1] >= hi:
                                    e -= 1
                                if not e:
                                    continue
                                lst = lst[:e]
                            if cands is None:
                                cands = lst
                            elif type(cands) is list:
                                cands = set(cands)
                                cands.update(lst)
                            else:
                                cands.update(lst)
                    if cands:
                        for y in cands:
                            o = sets[y]
                            m = lens[y]
                            r = req[m]
                            if (o <= s) if r == m else (len(s & o) >= r):
                                pairs.append((o, s))
                if q0 <= k:
                    continue
                for t in toks[k:q0]:
                    lst = index.get(t)
                    if lst is None:
                        index[t] = [x]
                    else:
                        lst.append(x)
            start = end
        if groups is None:
            for a, b in pairs:
                i = ids[a]
                j = ids[b]
                out.append((i, j) if i < j else (j, i))
        else:
            get = groups.get
            for a, b in pairs:
                for i in get(a) or (ids[a],):
                    for j in get(b) or (ids[b],):
                        out.append((i, j) if i < j else (j, i))
    return out
