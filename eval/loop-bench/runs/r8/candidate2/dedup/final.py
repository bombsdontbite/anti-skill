from collections import Counter
from itertools import chain


def near_duplicates(records):
    fs = list(map(frozenset, map(str.split, records)))
    nrec = len(fs)
    first = dict(zip(reversed(fs), range(nrec - 1, -1, -1)))
    empty = frozenset()
    first.pop(empty, None)
    pairs = []
    append = pairs.append
    groups = {}
    if len(first) + (empty in fs) < nrec or empty in fs and fs.count(empty) > 1:
        for i, f in enumerate(map(first.get, fs)):
            if f is not None and f != i:
                g = groups.get(f)
                if g is None:
                    groups[f] = g = [f]
                for x in g:
                    append((x, i))
                g.append(i)

    def emit(a, j):
        ga = groups.get(a)
        gb = groups.get(j)
        if ga is None and gb is None:
            append((a, j) if a < j else (j, a))
        else:
            for x in ga or (a,):
                for y in gb or (j,):
                    append((x, y) if x < y else (y, x))

    # When the smaller set has at most 7 tokens, 5|A&B| >= 4|A|B| forces A to be B minus
    # one token, with B of 5 to 8 tokens.
    get = first.get
    # Sum of token hashes of each 4- to 7-token set: B minus x can only be one of them if
    # the sums agree, which is far cheaper to test than building B minus x.
    hs = {sum(map(hash, s)) for s in first if 3 < len(s) < 8}
    big = []
    for s, j in first.items():
        m = len(s)
        if m < 5:
            continue
        if m > 7:
            big.append(s)
            if m > 8:
                continue
        h = sum(map(hash, s))
        for x in s:
            if h - hash(x) not in hs:
                continue
            a = get(s - {x})
            if a is not None:
                if groups:
                    emit(a, j)
                else:
                    append((a, j) if a < j else (j, a))

    # Both sets have 8 tokens or more: prefix filter, rarest tokens first.
    if len(big) < 2:
        return pairs
    sets = sorted(big, key=len)
    freq = Counter(chain.from_iterable(sets))
    order = sorted(freq, key=freq.get)
    rank = dict(zip(order, range(len(order)))).get
    single = list(freq.values()).count(1)
    index = [[] for _ in range(len(order) - single)]
    for k, s in enumerate(sets):
        n = len(s)
        minlen = (4 * n + 4) // 5
        prefix = sorted(map(rank, s))[:n - minlen + 1]
        if prefix[-1] < single:
            continue
        cands = set()
        for t in prefix:
            if t >= single:
                lst = index[t - single]
                cands.update(lst)
                lst.append(k)
        if cands:
            a = first[s]
            for c in cands:
                b = sets[c]
                m = len(b)
                if m < minlen:
                    continue
                inter = len(s & b)
                if 5 * inter >= 4 * (n + m - inter):
                    if groups:
                        emit(a, first[b])
                    else:
                        j = first[b]
                        append((a, j) if a < j else (j, a))
    return pairs
