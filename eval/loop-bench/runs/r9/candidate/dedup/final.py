from collections import Counter
from itertools import chain


def near_duplicates(records):
    groups = {}
    for i, s in enumerate(map(frozenset, map(str.split, records))):
        if s:
            g = groups.get(s)
            if g is None:
                groups[s] = [i]
            else:
                g.append(i)
    pairs = []
    append = pairs.append
    gget = groups.get
    big = []
    for s, idx in groups.items():
        if len(idx) > 1:
            for a in range(len(idx)):
                ia = idx[a]
                for b in idx[a + 1:]:
                    append((ia, b))
        la = len(s)
        if la > 7:
            big.append(s)
        if 4 < la < 9:
            # up to 8 tokens, the only non-identical partners are the set minus one token
            for e in s:
                other = gget(s - {e})
                if other:
                    for i in idx:
                        for j in other:
                            append((i, j) if i < j else (j, i))
    # sets of 9+ tokens can only pair with sets of 8+ tokens
    sets = big
    if len(sets) < 40:
        # too few sets for the index to pay for its setup
        for x, s in enumerate(sets):
            la = len(s)
            for ys in sets[x + 1:]:
                if 9 * len(s & ys) >= 4 * (la + len(ys)):
                    for i in groups[s]:
                        for j in groups[ys]:
                            append((i, j) if i < j else (j, i))
        return pairs
    freq = Counter(chain.from_iterable(sets))
    rank = {t: k for k, t in enumerate(sorted(freq, key=freq.get))}
    rget = rank.get
    sets.sort(key=len)
    lens = [len(s) for s in sets]
    index = {}
    start = {}
    for x, s in enumerate(sets):
        la = lens[x]
        minlen = (4 * la + 4) // 5
        toks = sorted(map(rget, s))
        if la > 8:
            cands = set()
            for t in toks[:la - minlen + 1]:
                lst = index.get(t)
                if lst:
                    st = start[t]
                    n = len(lst)
                    if st < n and lens[lst[st]] < minlen:
                        st += 1
                        while st < n and lens[lst[st]] < minlen:
                            st += 1
                        start[t] = st
                    if st == 0:
                        cands.update(lst)
                    elif st < n:
                        cands.update(lst[st:])
            if cands:
                ids = groups[s]
                for y in [y for y in cands if 9 * len(s & sets[y]) >= 4 * (la + lens[y])]:
                    ys = sets[y]
                    for i in ids:
                        for j in groups[ys]:
                            append((i, j) if i < j else (j, i))
        for t in toks[:la - (8 * la + 8) // 9 + 1]:
            lst = index.get(t)
            if lst is None:
                index[t] = [x]
                start[t] = 0
            else:
                lst.append(x)
    return pairs
