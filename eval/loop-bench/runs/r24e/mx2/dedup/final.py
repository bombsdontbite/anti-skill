from itertools import count, repeat


def near_duplicates(records):
    # Each token's id is minus the position of its first occurrence: a global order in which
    # tokens first seen latest, which tend to be rare, come first.
    ids = {}
    sl = list(map(frozenset, map(map, repeat(ids.setdefault), map(str.split, records), repeat(count(0, -1)))))
    nrec = len(sl)
    first = dict(zip(reversed(sl), range(nrec - 1, -1, -1)))
    first.pop(frozenset(), None)
    pairs = []
    dup = {}
    if len(first) < nrec:
        for i in sorted(set(range(nrec)).difference(first.values())):
            f = first.get(sl[i])
            if f is not None:
                g = dup.get(f)
                if g is None:
                    dup[f] = [f, i]
                else:
                    g.append(i)
        for g in dup.values():
            for a in range(len(g)):
                ga = g[a]
                for b in g[a + 1:]:
                    pairs.append((ga, b))
    # Distinct sets of 3 tokens or fewer reach 0.8 with no other set.
    sets = sorted([s for s in first if len(s) > 3], key=len)
    if not sets:
        return pairs
    srt = list(map(sorted, sets))
    lens = list(map(len, sets))
    total = len(sets)
    index = {}
    get = index.get
    # Below 9 tokens the only partners are subsets with one token fewer; sets under 8 tokens
    # are kept in one dict per size, keyed by their first token.
    prev = {}
    k = 0
    while k < total and lens[k] < 9:
        n = lens[k]
        end = k
        while end < total and lens[end] == n:
            end += 1
        cur = {} if n < 8 else index
        for k in range(k, end):
            pre = srt[k]
            s = sets[k]
            if n > 4:
                lst = prev.get(pre[0])
                if lst:
                    for y in lst:
                        if y < s:
                            add(pairs, dup, first[s], first[y])
                lst = prev.get(pre[1])
                if lst:
                    for y in lst:
                        if y < s:
                            add(pairs, dup, first[s], first[y])
            t = pre[0]
            lst = cur.get(t)
            if lst is None:
                cur[t] = [s]
            else:
                lst.append(s)
        prev = cur if end < total and lens[end] == n + 1 else {}
        k = end
    for k in range(k, total):
        n = lens[k]
        pre = srt[k]
        s = sets[k]
        cands = set()
        for t in pre[:n - (4 * n + 4) // 5 + 1]:
            lst = get(t)
            if lst:
                cands.update(lst)
        if cands:
            mn = (4 * n + 4) // 5
            sub = (4 * n + 13) // 5
            for y in cands:
                m = len(y)
                # Below sub tokens a partner must be a subset.
                if m >= mn and ((y < s) if m < sub else 9 * len(s & y) >= 4 * (n + m)):
                    add(pairs, dup, first[s], first[y])
        for t in pre[:n - (8 * n + 8) // 9 + 1]:
            lst = get(t)
            if lst is None:
                index[t] = [s]
            else:
                lst.append(s)
    return pairs


def add(pairs, dup, a, b):
    if a in dup or b in dup:
        for u in dup.get(a, (a,)):
            for v in dup.get(b, (b,)):
                pairs.append((u, v) if u < v else (v, u))
    else:
        pairs.append((a, b) if a < b else (b, a))
