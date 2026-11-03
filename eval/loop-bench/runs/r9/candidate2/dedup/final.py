from itertools import chain, combinations, repeat
from operator import lshift


def near_duplicates(records):
    fs = list(map(frozenset, map(str.split, records)))
    groups = {}
    for i, s in enumerate(fs):
        g = groups.get(s)
        if g is None:
            groups[s] = [i]
        else:
            g.append(i)
    groups.pop(frozenset(), None)
    pairs = []
    for g in groups.values():
        if len(g) > 1:
            pairs.extend(combinations(g, 2))
    # sets of 3 or fewer tokens are only ever alike to an identical set
    sets = sorted([s for s in groups if len(s) > 3], key=len)
    lens = list(map(len, sets))
    if len(sets) ** 2 <= sum(lens):
        # few, huge sets: comparing every pair is cheaper than indexing their tokens
        for x, s in enumerate(sets):
            n4 = 4 * lens[x]
            for y in range(x):
                if 9 * len(s & sets[y]) >= n4 + 4 * lens[y]:
                    for i in groups[s]:
                        for j in groups[sets[y]]:
                            pairs.append((i, j) if i < j else (j, i))
        return pairs
    # the order only has to be consistent; frequencies from a third of the sets suffice
    df = dict.fromkeys(chain.from_iterable(sets), 0)
    for t in chain.from_iterable(sets[::3]):
        df[t] += 1
    rank = dict(zip(sorted(df, key=df.__getitem__), range(len(df))))
    key = rank.__getitem__
    ordered = [sorted(map(key, s)) for s in sets]
    masks = [0] * len(sets)
    index = {}
    get = index.get
    # first[k]: position of the first set with at least k tokens
    first = []
    for x, n in enumerate(lens):
        while len(first) <= n:
            first.append(x)
    for x, toks in enumerate(ordered):
        n = lens[x]
        minlen = (4 * n + 4) // 5
        lo = first[minlen]
        cands = set()
        for t in toks[:n - minlen + 1]:
            lst = get(t)
            if lst is not None:
                # lst[0] is where its sets long enough begin; lo never decreases
                p = lst[0]
                end = len(lst)
                if p < end and lst[p] < lo:
                    p += 1
                    while p < end and lst[p] < lo:
                        p += 1
                    lst[0] = p
                if p < end:
                    cands.update(lst[p:])
        # a smaller partner needs an overlap of at least 8/9 of its own size
        for t in toks[:n - (8 * n + 8) // 9 + 1]:
            lst = get(t)
            if lst is None:
                index[t] = [1, x]
            else:
                lst.append(x)
        if not cands:
            continue
        s = sets[x]
        if len(cands) < 8:
            hits = [y for y in cands if 5 * (k := len(s & sets[y])) >= 4 * (n + lens[y] - k)]
        else:
            # many candidates: bitmask intersections beat set intersections
            mask = masks[x] = sum(map(lshift, repeat(1), toks))
            hits = []
            for y in cands:
                my = masks[y]
                if not my:
                    my = masks[y] = sum(map(lshift, repeat(1), ordered[y]))
                k = (mask & my).bit_count()
                if 5 * k >= 4 * (n + lens[y] - k):
                    hits.append(y)
        gx = groups[s]
        for y in hits:
            for i in gx:
                for j in groups[sets[y]]:
                    pairs.append((i, j) if i < j else (j, i))
    return pairs
