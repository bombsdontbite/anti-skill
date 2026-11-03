from bisect import bisect_left, bisect_right
from collections import Counter
from itertools import chain


def near_duplicates(records):
    split = list(map(str.split, records))
    # Counting occurrences rather than records only steers the token order, which any fixed order keeps exact.
    df = Counter(chain.from_iterable(split))
    sets = list(map(set, split))
    words = sorted(df, key=df.get)
    rget = dict(zip(words, range(len(words)))).get
    # Tokens ranked below this occur in one record only and can never be shared.
    first_shared = list(df.values()).count(1)
    lens = list(map(len, sets))
    by_len = [[] for _ in range(max(lens, default=0) + 1)]
    for x, a in enumerate(lens):
        by_len[a].append(x)
    ids = {}
    sizes = {}
    iget = ids.get
    sget = sizes.get
    left = bisect_left
    right = bisect_right
    pairs = []
    append = pairs.append
    for a in range(1, len(by_len)):
        minb = (4 * a + 4) // 5
        p = a - minb + 1
        m = a - (8 * a + 8) // 9 + 1
        # A shared token at position i leaves room for a partner of size at most (5a - 9i) // 4.
        his = [min(a, (5 * a - 9 * i) // 4) for i in range(p)]
        for x in by_len[a]:
            s = sets[x]
            toks = sorted(s, key=rget)
            if rget(toks[p - 1]) < first_shared:
                continue
            cands = None
            for i in range(p):
                w = toks[i]
                sz = sget(w)
                if sz:
                    c = ids[w][left(sz, minb):right(sz, his[i])]
                    if cands is None:
                        cands = c
                    elif c:
                        cands = set(cands).union(c)
            if cands:
                for y in cands:
                    t = sets[y]
                    if 9 * len(s & t) >= 4 * (a + len(t)):
                        append((x, y) if x < y else (y, x))
            for w in toks[:m]:
                lst = iget(w)
                if lst is None:
                    ids[w] = [x]
                    sizes[w] = [a]
                else:
                    lst.append(x)
                    sizes[w].append(a)
    return pairs
