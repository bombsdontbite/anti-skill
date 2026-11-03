def near_duplicates(records):
    sets = list(map(set, map(str.split, records)))
    u = set().union(*sets)
    big = len(u)
    cnt = dict(zip(u, range(big)))
    for s in sets[::4]:
        for t in s:
            cnt[t] += big
    rk = cnt.get
    order = [i for _, i in sorted(zip(map(len, sets), range(len(sets))))]
    ss = [sets[i] for i in order]
    top = len(ss[-1]) if ss else 0
    end = [0] * (top + 2)
    for s in ss:
        end[len(s)] += 1
    for n in range(1, top + 2):
        end[n] += end[n - 1]
    index = {}
    iget = index.get
    pairs = []
    k = end[0] - 1
    for a in ss[end[0]:]:
        k += 1
        la = len(a)
        toks = sorted(a, key=rk)
        lo = (4 * la + 4) // 5
        kmin = end[lo - 1]
        m = la - (8 * la + 8) // 9 + 1
        cands = set()
        for t in toks[:m]:
            lst = iget(t)
            if lst is None:
                index[t] = [k]
            else:
                if lst and lst[0] < kmin:
                    n = 1
                    while n < len(lst) and lst[n] < kmin:
                        n += 1
                    del lst[:n]
                cands.update(lst)
                lst.append(k)
        p = m
        for t in toks[m:la - lo + 1]:
            lst = iget(t)
            if lst:
                if lst[0] < kmin:
                    n = 1
                    while n < len(lst) and lst[n] < kmin:
                        n += 1
                    del lst[:n]
                kend = end[(5 * la - 9 * p) // 4]
                if lst and lst[-1] >= kend:
                    n = len(lst) - 1
                    while n and lst[n - 1] >= kend:
                        n -= 1
                    cands.update(lst[:n])
                else:
                    cands.update(lst)
            p += 1
        for j in cands:
            b = ss[j]
            if 9 * len(a & b) >= 4 * (la + len(b)):
                x = order[k]
                y = order[j]
                pairs.append((x, y) if x < y else (y, x))
    return pairs
