from collections import Counter
from itertools import chain


def near_duplicates(records):
    sets = [set(r.split()) for r in records]
    freq = Counter(chain.from_iterable(sets))
    rank = {t: k for k, t in enumerate(sorted(freq, key=freq.get))}
    get = rank.get
    sizes = [len(s) for s in sets]
    order = sorted(range(len(sets)), key=lambda i: sizes[i])
    index = {}
    iget = index.get
    pairs = []
    app = pairs.append
    for i in order:
        a = sizes[i]
        if not a:
            continue
        s = sets[i]
        p = a - (4 * a + 4) // 5 + 1
        pref = sorted(s, key=get)[:p] if p < a else s
        lo = 4 * a
        cand = set()
        for t in pref:
            lst = iget(t)
            if lst is None:
                index[t] = [i]
            else:
                cand.update(lst)
                lst.append(i)
        for j in cand:
            b = sizes[j]
            if 5 * b >= lo:
                inter = len(s & sets[j])
                if 5 * inter >= 4 * (a + b - inter):
                    app((j, i) if j < i else (i, j))
    return pairs
