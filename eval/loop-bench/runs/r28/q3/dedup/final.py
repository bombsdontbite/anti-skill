from collections import Counter
from itertools import chain


def near_duplicates(records):
    groups = {}
    gg = groups.get
    for i, s in enumerate(map(frozenset, map(str.split, records))):
        g = gg(s)
        if g is None:
            groups[s] = [i]
        else:
            g.append(i)
    groups.pop(frozenset(), None)
    pairs = []
    for g in groups.values():
        if len(g) > 1:
            for x in range(len(g)):
                gx = g[x]
                for y in g[x + 1:]:
                    pairs.append((gx, y))
    uniq = sorted(groups, key=len)
    freq = Counter(chain.from_iterable(uniq))
    rank = {w: i for i, w in enumerate(sorted(freq, key=freq.get))}
    rk = rank.get
    index = [None] * len(rank)
    sizes = [len(u) for u in uniq]
    for k, s in enumerate(uniq):
        n = len(s)
        toks = sorted(map(rk, s))
        lo = (4 * n + 4) // 5
        if n < 5:
            cands = index[toks[0]]
        else:
          cands = None
          for w in toks[:n - lo + 1]:
              lst = index[w]
              if lst:
                  if cands is None:
                      cands = set(lst)
                  else:
                      cands.update(lst)
        if cands:
            gs = groups[s]
            for c in cands:
                m = sizes[c]
                if m >= lo:
                    t = uniq[c]
                    inter = len(s & t)
                    if 5 * inter >= 4 * (n + m - inter):
                        for a in gs:
                            for b in groups[t]:
                                pairs.append((a, b) if a < b else (b, a))
        for w in toks[:n - (8 * n + 8) // 9 + 1]:
            lst = index[w]
            if lst is None:
                index[w] = [k]
            else:
                lst.append(k)
    return pairs
