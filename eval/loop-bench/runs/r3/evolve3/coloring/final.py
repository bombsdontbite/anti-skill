import random, time

LIMIT = 0.6

def rlf(n, adj):
    colors = [-1] * n
    U = set(range(n)); c = 0
    while U:
        degU = {u: len(adj[u] & U) for u in U}
        V = set(U); W = set(); cls = []
        x = max(V, key=lambda u: degU[u])
        while True:
            cls.append(x); V.discard(x)
            nb = adj[x] & V
            V.difference_update(nb); W.update(nb)
            if not V: break
            x = max(V, key=lambda u: (len(adj[u] & W), -len(adj[u] & V)))
        for y in cls: colors[y] = c
        U.difference_update(cls); c += 1
    return colors

def tabucol(n, adjl, k, col, deadline, rng):
    gamma = [[0] * k for _ in range(n)]
    for u in range(n):
        g = gamma[u]
        for v in adjl[u]: g[col[v]] += 1
    conf = 0
    cset = set()
    for u in range(n):
        if gamma[u][col[u]]: conf += gamma[u][col[u]]; cset.add(u)
    conf //= 2
    if conf == 0: return col
    tabu = [[0] * k for _ in range(n)]
    best = conf; it = 0
    rk = range(k)
    while True:
        it += 1
        if (it & 127) == 0 and time.time() > deadline: return None
        bd = 1 << 30; moves = []
        for u in cset:
            g = gamma[u]; cu = col[u]; gu = g[cu]
            tu = tabu[u]
            for c in rk:
                d = g[c] - gu
                if d > bd or c == cu: continue
                if tu[c] > it and conf + d >= best: continue
                if d < bd: bd = d; moves = [(u, c)]
                else: moves.append((u, c))
        if not moves:
            continue
        u, c = moves[rng.randrange(len(moves))]
        old = col[u]
        col[u] = c
        for v in adjl[u]:
            gv = gamma[v]; gv[old] -= 1; gv[c] += 1
            cv = col[v]
            if cv == old and gv[old] == 0: cset.discard(v)
            elif cv == c and gv[c] == 1: cset.add(v)
        if gamma[u][c]: cset.add(u)
        else: cset.discard(u)
        conf += bd
        tabu[u][old] = it + int(0.6 * len(cset)) + rng.randrange(10)
        if conf < best: best = conf
        if conf == 0: return col

def color(n, edges):
    t0 = time.time(); deadline = t0 + LIMIT
    rng = random.Random(12345)
    adj = [set() for _ in range(n)]
    for u, v in edges:
        adj[u].add(v); adj[v].add(u)
    adjl = [list(a) for a in adj]
    best = rlf(n, adj)
    k = max(best) + 1 if n else 0
    while k > 1 and time.time() < deadline:
        k1 = k - 1
        cnt = [0] * k
        for c in best: cnt[c] += 1
        drop = min(range(k), key=lambda c: cnt[c])
        col = [(c if c < drop else c - 1) if c != drop else rng.randrange(k1) for c in best]
        res = tabucol(n, adjl, k1, col, deadline, rng)
        if res is None: break
        best = res[:]; k = k1
    # renumber
    m = {}
    return [m.setdefault(c, len(m)) for c in best]
