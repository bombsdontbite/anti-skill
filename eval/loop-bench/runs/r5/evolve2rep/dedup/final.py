def near_duplicates(records):
    groups = {}
    gget = groups.get
    for i, s in enumerate(map(frozenset, map(str.split, records))):
        g = gget(s)
        if g is None:
            groups[s] = [i]
        else:
            g.append(i)
    groups.pop(frozenset(), None)
    pairs = []
    app = pairs.append
    for g in groups.values():
        if len(g) > 1:
            for k, u in enumerate(g):
                for v in g[k + 1:]:
                    app((u, v))
    # up to 8 words, a match is an identical set or a superset with one more word
    for b, gb in groups.items():
        if 4 < len(b) < 9:
            for t in b:
                a = b.difference((t,))
                if a in groups:
                    for u in groups[a]:
                        for v in gb:
                            app((u, v) if u < v else (v, u))
    big = [s for s in groups if len(s) > 7]
    if not big or max(map(len, big)) < 9:
        return pairs
    uniq = sorted(big, key=len)
    gl = list(map(groups.get, uniq))
    L = list(map(len, uniq))
    cnt = {}
    cg = cnt.get
    k = 0
    for a in big:
        for t in a:
            cnt[t] = cg(t, 0) + 1
        k += 1
        if k >= 400:
            break
    srt = [t for t in sorted(cnt, key=cnt.get) if cnt[t] > 1]
    rg = dict(zip(srt, range(len(srt)))).get
    common = frozenset(srt)
    nu = len(uniq)
    first = []
    x = 0
    for s in range(L[-1] + 1):
        while L[x] < s:
            x += 1
        first.append(x)
    SH = L[-1].bit_length() + 1
    MK = (1 << SH) - 1
    index = {}
    ig = index.get
    x9 = first[9]
    for x in range(x9):
        r = uniq[x] - common
        t = min(r) if r else min(map(rg, uniq[x]))
        lst = ig(t)
        if lst is None:
            index[t] = [x << SH]
        else:
            lst.append(x << SH)
    for x in range(x9, nu):
        a = uniq[x]
        n = L[x]
        p = n - (4 * n + 4) // 5 + 1
        toks = sorted(a - common)
        if len(toks) < p:
            toks += sorted(map(rg, a & common))
        lo = first[(4 * n + 4) // 5] << SH
        seen = set()
        gx = gl[x]
        ri = n + 1
        for t in toks[:p]:
            ri -= 1
            lst = ig(t)
            if lst:
                if lst[0] < lo:
                    if lst[-1] < lo:
                        continue
                    k = len(lst) - 1
                    while lst[k - 1] >= lo:
                        k -= 1
                    lst = lst[k:]
                for e in lst:
                    y = e >> SH
                    if y in seen:
                        continue
                    seen.add(y)
                    m = L[y]
                    rj = m - (e & MK)
                    need = 4 * (n + m)
                    if 9 * (ri if ri < rj else rj) < need or 9 * len(a & uniq[y]) < need:
                        continue
                    for u in gx:
                        for v in gl[y]:
                            app((u, v) if u < v else (v, u))
        e = x << SH
        for t in toks[:n - (8 * n + 8) // 9 + 1]:
            lst = ig(t)
            if lst is None:
                index[t] = [e]
            else:
                lst.append(e)
            e += 1
    return pairs
