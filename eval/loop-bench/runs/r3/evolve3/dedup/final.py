from collections import Counter
from itertools import chain


def near_duplicates(records):
    # Prefix filtering: rare tokens first in one consistent total order, a shorter prefix indexed
    # than probed, candidates from earlier (not larger) records only, exact verification.
    groups = {}
    for i, s in enumerate(map(frozenset, map(str.split, records))):
        g = groups.get(s)
        if g is None:
            groups[s] = [i]
        else:
            g.append(i)
    groups.pop(frozenset(), None)
    uniq = sorted(groups, key=len)
    freq = Counter(chain.from_iterable(uniq))
    rank = {t: r for r, t in enumerate(sorted(freq, key=freq.__getitem__))}
    rget = rank.__getitem__
    index = {}
    iget = index.get
    pairs = []
    cur = -1
    lo = 0
    for k, s in enumerate(uniq):
        n = len(s)
        if n != cur:
            cur = n
            minsize = (4 * n + 4) // 5
            p = n - minsize + 1
            q = n - (8 * n + 8) // 9 + 1
            while len(uniq[lo]) < minsize:
                lo += 1
        if p == 1:
            t = min(s, key=rget)
            lst = iget(t)
            if lst is None:
                index[t] = [k]
                continue
            for y in lst:
                if y >= lo:
                    b = uniq[y]
                    inter = len(s & b)
                    if 5 * inter >= 4 * (n + len(b) - inter):
                        pairs.append((k, y))
            lst.append(k)
            continue
        cand = set()
        pre = sorted(s, key=rget)
        for t in pre[:q]:
            lst = iget(t)
            if lst is None:
                index[t] = [k]
            else:
                cand.update(lst)
                lst.append(k)
        for t in pre[q:p]:
            lst = iget(t)
            if lst is not None:
                cand.update(lst)
        for y in cand:
            if y >= lo:
                b = uniq[y]
                inter = len(s & b)
                if 5 * inter >= 4 * (n + len(b) - inter):
                    pairs.append((k, y))
    out = []
    for g in groups.values():
        L = len(g)
        if L > 1:
            for x in range(L):
                for z in range(x + 1, L):
                    out.append((g[x], g[z]))
    for k, y in pairs:
        gk = groups[uniq[k]]
        gy = groups[uniq[y]]
        if len(gk) == 1 and len(gy) == 1:
            i = gk[0]
            j = gy[0]
            out.append((i, j) if i < j else (j, i))
        else:
            for i in gk:
                for j in gy:
                    out.append((i, j) if i < j else (j, i))
    return out
