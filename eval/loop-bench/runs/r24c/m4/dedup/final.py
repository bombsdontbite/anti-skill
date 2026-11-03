from bisect import bisect_left
from collections import Counter
from itertools import chain


def near_duplicates(records):
    split = list(map(str.split, records))
    freq = Counter(chain.from_iterable(split))
    rank = dict(zip(sorted(freq, key=freq.get), range(len(freq))))
    toks = [tuple(sorted(set(map(rank.get, s)))) for s in split]
    last = {t: i for i, t in enumerate(toks)}
    pairs = []
    groups = {}
    if len(last) < len(toks):
        for i, t in enumerate(toks):
            if last[t] != i:
                g = groups.get(t)
                if g is None:
                    groups[t] = [i]
                else:
                    g.append(i)
        for t, g in groups.items():
            g.append(last[t])
            if t:
                for x in range(len(g)):
                    a = g[x]
                    for b in g[x + 1:]:
                        pairs.append((a, b))
    keys = [t for t in last if len(t) > 3]
    if not keys:
        return pairs
    keys.sort(key=len)
    sizes = list(map(len, keys))
    start = [bisect_left(sizes, m) for m in range(sizes[-1] + 1)]
    index = {}
    seen = set()
    dup = set()
    for k, s in enumerate(keys):
        n = sizes[k]
        size = n - (8 * n + 8) // 9 + 2
        if n < 5:
            for t in s[:size]:
                lst = index.get(t)
                if lst is None:
                    index[t] = [k]
                else:
                    lst.append(k)
            continue
        minlen = (4 * n + 4) // 5
        lo = start[minlen]
        for t in s[:size]:
            lst = index.get(t)
            if lst is None:
                index[t] = [k]
            else:
                if lst and lst[0] < lo:
                    del lst[:bisect_left(lst, lo)]
                dup |= seen.intersection(lst)
                seen.update(lst)
                lst.append(k)
        for t in s[size:n - minlen + 2]:
            lst = index.get(t)
            if lst:
                if lst[0] < lo:
                    del lst[:bisect_left(lst, lo)]
                dup |= seen.intersection(lst)
                seen.update(lst)
        if dup:
            mine = groups.get(s) or [last[s]]
            st = set(s)
            for o in dup:
                other = keys[o]
                inter = len(st.intersection(other))
                if 5 * inter >= 4 * (n + sizes[o] - inter):
                    for b in groups.get(other) or [last[other]]:
                        for a in mine:
                            pairs.append((a, b) if a < b else (b, a))
            dup.clear()
        seen.clear()
    return pairs
