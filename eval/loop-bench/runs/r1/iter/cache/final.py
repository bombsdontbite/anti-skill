# Predicted-next-use eviction (evict the key whose next request looks furthest away),
# with a family of variants simulated as shadows; the real cache adopts the
# parameters of whichever shadow has recently been hitting best.
from collections import OrderedDict
from itertools import islice
import heapq

INF = 1e18


class _P:
    def __init__(self, cap, beta, D, w1, P, nchk):
        self.st = OrderedDict()
        self.h = []
        self.cap = cap; self.nchk = nchk
        self.set(beta, D, w1, P)

    def set(self, beta, D, w1, P):
        self.beta = beta; self.D = D; self.w1 = w1; self.P = P

    def prio(self, t, i, n):
        if i is None:
            return t + self.D
        if self.P:
            return self.w1 * t + (n * i + self.P) / (n + 1)
        return self.w1 * t + i

    def rebuild(self, last, iv, nn):
        st = self.st
        for k in st:
            st[k] = self.prio(last[k], iv.get(k), nn.get(k, 0))
        self.h = [(-p, k) for k, p in st.items()]; heapq.heapify(self.h)

    def step(self, key, t, i, n, last, iv):
        st = self.st
        pred = self.prio(t, i, n)
        if key in st:
            st[key] = pred; st.move_to_end(key)
            heapq.heappush(self.h, (-pred, key))
            return 1
        if len(st) >= self.cap:
            victim = None
            beta = self.beta; D = self.D
            for v in islice(st, self.nchk):
                vi = iv.get(v)
                if t - last[v] > beta * (vi if vi is not None else D):
                    victim = v; break
            if victim is None:
                h = self.h
                while True:
                    np_, k = h[0]
                    if st.get(k) == -np_: break
                    heapq.heappop(h)
                if pred >= -np_:
                    return 0
                heapq.heappop(h); victim = k
            del st[victim]
        st[key] = pred
        heapq.heappush(self.h, (-pred, key))
        if len(self.h) > 8 * self.cap:
            self.h = [(-p, k) for k, p in st.items()]; heapq.heapify(self.h)
        return 0


class Cache:
    def __init__(self, capacity, grid=None, alpha=0.4, gk=8, z=1.0, w1=0.5, nchk=3, start=1, nmax=8, rb=True):
        self.capacity = capacity
        if grid is None:
            grid = [(0.0, INF), (1.2, INF), (1.5, INF), (2.0, INF), (3.0, INF), (1.5, 2.0), (1.5, 8.0),
                    (1.2, INF, 0.5, 1000), (2.0, INF, 0.5, 1000), (3.0, INF, 0.5, 1000), (5.0, INF, 0.5, 1000), (100.0, INF, 0.5, 1000)]
        self.grid = [(g[0], g[1] * capacity if g[1] < INF else INF, g[2] if len(g) > 2 else w1,
                      g[3] * capacity if len(g) > 3 else 0) for g in grid]
        self.sh = [_P(capacity, *g, nchk) for g in self.grid]
        self.sc = [0.0] * len(self.sh)
        self.g = 1.0 - 1.0 / (gk * capacity)
        self.z = z
        self.best = start
        self.real = _P(capacity, *self.grid[start], nchk)
        self.store = self.real.st
        self.last = {}; self.iv = {}; self.n = {}; self.t = 0
        self.alpha = alpha; self.nmax = nmax; self.rb = rb

    def access(self, key):
        if self.capacity <= 0:
            return False
        t = self.t = self.t + 1
        last = self.last; iv = self.iv
        lt = last.get(key)
        n = 0
        if lt is not None:
            # per-key EMA of the reuse interval; n = re-reference count, capped
            d = t - lt
            o = iv.get(key)
            iv[key] = d if o is None else o + self.alpha * (d - o)
            n = self.n.get(key, 0)
            if n < self.nmax:
                n += 1; self.n[key] = n
        i = iv.get(key)
        last[key] = t
        sc = self.sc; g = self.g
        for j, p in enumerate(self.sh):
            sc[j] = sc[j] * g + p.step(key, t, i, n, last, iv)
        b = 0; bv = sc[0]
        for j in range(1, len(sc)):
            if sc[j] > bv:
                b = j; bv = sc[j]
        if b != self.best:
            c = sc[self.best]
            if sc[b] - c > self.z * (sc[b] + c + 1) ** 0.5:
                self.best = b
                self.real.set(*self.grid[b])
                if self.rb: self.real.rebuild(self.last, self.iv, self.n)
        return self.real.step(key, t, i, n, last, iv) == 1
