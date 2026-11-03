import random
import time
from operator import sub

BUDGET = 0.85
ALPHA = 0.4
RT = 15
INIT = 2


def _bits(x):
    out = []
    while x:
        low = x & -x
        out.append(low.bit_length() - 1)
        x ^= low
    return out


def _greedy_order(n, adj, order):
    colors = [-1] * n
    for u in order:
        taken = {colors[v] for v in adj[u]}
        c = 0
        while c in taken:
            c += 1
        colors[u] = c
    return colors


def _ncol(colors):
    return len(set(colors))


def _normalize(colors):
    m = {}
    out = []
    for c in colors:
        if c not in m:
            m[c] = len(m)
        out.append(m[c])
    return out


def _rlf(n, N, pw):
    colors = [-1] * n
    U = (1 << n) - 1
    c = 0
    while U:
        P = U
        W = 0
        # first vertex: most neighbours among the uncoloured
        best = -1
        bv = -1
        for v in _bits(P):
            d = (N[v] & U).bit_count()
            if d > best:
                best = d
                bv = v
        while True:
            colors[bv] = c
            b = pw[bv]
            U ^= b
            W |= N[bv] & U
            P &= ~(N[bv] | b)
            if not P:
                break
            best = -1
            bv = -1
            if W:
                for v in _bits(P):
                    d = (N[v] & W).bit_count()
                    if d > best:
                        best = d
                        bv = v
            else:
                for v in _bits(P):
                    d = (N[v] & P).bit_count()
                    if d > best:
                        best = d
                        bv = v
        c += 1
    return colors


def _clique_lb(n, N, deg, deadline):
    best = 1
    order = sorted(range(n), key=lambda x: -deg[x])
    for s in order[:20]:
        if time.perf_counter() > deadline:
            break
        cand = N[s]
        size = 1
        while cand:
            bv = -1
            bd = -1
            for v in _bits(cand):
                d = (N[v] & cand).bit_count()
                if d > bd:
                    bd = d
                    bv = v
            cand &= N[bv]
            size += 1
        if size > best:
            best = size
    return best


def _greedy_k(n, N, k, rng):
    order = list(range(n))
    rng.shuffle(order)
    C = [0] * k
    col = [0] * n
    for v in order:
        Nv = N[v]
        cnt = [(Nv & Cc).bit_count() for Cc in C]
        m = min(cnt)
        c = rng.choice([i for i in range(k) if cnt[i] == m])
        col[v] = c
        C[c] |= 1 << v
    return col


def _bipartite(n, adj):
    col = [-1] * n
    for s in range(n):
        if col[s] >= 0:
            continue
        col[s] = 0
        stack = [s]
        while stack:
            u = stack.pop()
            for v in adj[u]:
                if col[v] < 0:
                    col[v] = 1 - col[u]
                    stack.append(v)
                elif col[v] == col[u]:
                    return None
    return col


def _tabucol(n, adj, k, colors, rng, deadline, N):
    """Bitset tabucol with tabu folded into the move rows; (True, colouring) or (False, state)."""
    col = list(colors)
    C = [0] * k
    for v in range(n):
        C[col[v]] |= 1 << v
    BIG = 1 << 40
    TB = 1 << 20
    LIM = TB >> 1
    rows = {}
    own = {}
    CF = 0
    f = 0
    for v in range(n):
        Nv = N[v]
        cv = col[v]
        if Nv & C[cv]:
            r = [(Nv & Cc).bit_count() for Cc in C]
            own[v] = r[cv]
            f += r[cv]
            r[cv] = BIG
            rows[v] = r
            CF |= 1 << v
    f //= 2
    if f == 0:
        return True, col
    tabu = [[0] * k for _ in range(n)]
    exp = {}
    best_f = f
    it = 0
    rint = rng.randrange
    rnd = rng.random
    choice = rng.choice
    perf = time.perf_counter
    while True:
        it += 1
        if (it & 31) == 0 and perf() > deadline:
            return False, col
        ev = exp.pop(it, None)
        if ev:
            for v, c in ev:
                if tabu[v][c] == it and v in rows and col[v] != c:
                    rows[v][c] -= TB
        ks = list(rows)
        ds = list(map(sub, map(min, rows.values()), own.values()))
        bd = min(ds)
        if bd < LIM:
            L = len(ds)
            s0 = int(rnd() * L)
            try:
                j = ds.index(bd, s0)
            except ValueError:
                j = ds.index(bd)
            bv = ks[j]
            g = rows[bv]
            m = bd + own[bv]
            s0 = int(rnd() * k)
            try:
                bc = g.index(m, s0)
            except ValueError:
                bc = g.index(m)
        else:
            bv = choice(ks)
            bc = rint(k - 1)
            if bc >= col[bv]:
                bc += 1
            bd = (rows[bv][bc] & (TB - 1)) - own[bv]
        old = col[bv]
        bit = 1 << bv
        Nb = N[bv]
        C[old] ^= bit
        C[bc] |= bit
        col[bv] = bc
        f += bd
        r = rows[bv]
        e = it + 1 + int(ALPHA * len(ks) + rnd() * RT)
        tabu[bv][old] = e
        bucket = exp.get(e)
        if bucket is None:
            exp[e] = [(bv, old)]
        else:
            bucket.append((bv, old))
        r[old] = own[bv] + TB
        own[bv] = r[bc] & (TB - 1)
        r[bc] = BIG
        x = Nb & CF
        while x:
            low = x & -x
            x ^= low
            u = low.bit_length() - 1
            r = rows[u]
            cu = col[u]
            if cu == old:
                own[u] -= 1
            else:
                r[old] -= 1
            if cu == bc:
                own[u] += 1
            else:
                r[bc] += 1
        x = Nb & C[old]
        while x:
            low = x & -x
            x ^= low
            u = low.bit_length() - 1
            if own[u] == 0:
                del rows[u]
                del own[u]
                CF ^= low
        x = Nb & C[bc] & ~CF
        while x:
            low = x & -x
            x ^= low
            u = low.bit_length() - 1
            Nu = N[u]
            r = [(Nu & Cc).bit_count() + (TB if t > it else 0) for Cc, t in zip(C, tabu[u])]
            own[u] = r[bc] & (TB - 1)
            r[bc] = BIG
            rows[u] = r
            CF |= low
        if own[bv] == 0:
            del rows[bv]
            del own[bv]
            CF ^= bit
        if f < best_f:
            best_f = f
            if f == 0:
                return True, col


def color(n, edges):
    t0 = time.perf_counter()
    deadline = t0 + BUDGET
    if n == 0:
        return []
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    if not edges:
        return [0] * n
    bip = _bipartite(n, adj)
    if bip is not None:
        return bip
    rng = random.Random(12345)
    deg = [len(a) for a in adj]
    pw = [1 << v for v in range(n)]
    N = [sum([pw[v] for v in a]) for a in adj]

    best = _greedy_order(n, adj, sorted(range(n), key=lambda u: (-deg[u], u)))
    if INIT == 2:
        r = _rlf(n, N, pw)
        if _ncol(r) <= _ncol(best):
            best = r
    best = _normalize(best)
    lb = _clique_lb(n, N, deg, t0 + 0.02)
    bk = _ncol(best)
    while bk > lb and time.perf_counter() < deadline:
        k = bk - 1
        sizes = [0] * bk
        for c in best:
            sizes[c] += 1
        drop = min(range(bk), key=lambda c: sizes[c])
        remap = [c if c < drop else c - 1 for c in range(bk)]
        init = [remap[c] if c != drop else -1 for c in best]
        for u in range(n):
            if init[u] < 0:
                cnt = [0] * k
                for v in adj[u]:
                    if init[v] >= 0:
                        cnt[init[v]] += 1
                m = min(cnt)
                init[u] = rng.choice([c for c in range(k) if cnt[c] == m])
        ok, res = _tabucol(n, adj, k, init, rng, deadline, N)
        if not ok:
            break
        best = _normalize(res)
        bk = _ncol(best)
    return best
