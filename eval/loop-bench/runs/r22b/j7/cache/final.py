from collections import OrderedDict
import heapq


class LIRS:
    def __init__(self, capacity, hc, ghost_mult, freq=None):
        self.c = capacity; self.hc = hc; self.freq = freq; self.guard = False
        self.S = OrderedDict(); self.Q = OrderedDict(); self.NR = OrderedDict()
        self.lir = set(); self.store = set()
        self.maxS = capacity * (1 + ghost_mult)

    def _prune(self):
        S, lir = self.S, self.lir
        while S:
            k = next(iter(S))
            if k in lir: break
            del S[k]

    def _ok(self, key):
        f = self.freq
        if not self.guard or len(self.lir) < self.c - self.hc: return True
        S = self.S
        b = next(iter(S))
        return f.get(key) >= f.get(b)

    def _demote(self):
        S = self.S
        k = next(iter(S)); self.lir.discard(k); del S[k]; self.Q[k] = None
        self._prune()

    def access(self, key):
        S, Q, lir, store = self.S, self.Q, self.lir, self.store
        if key in lir:
            S.move_to_end(key); self._prune(); return True
        if key in store:
            if key in S and self._ok(key):
                del S[key]; S[key] = None; del Q[key]
                lir.add(key)
                if len(lir) > self.c - self.hc: self._demote()
            else:
                S[key] = None; Q.move_to_end(key)
            return True
        self.NR.pop(key, None)
        lc = self.c - self.hc
        if len(lir) < lc and len(store) < self.c:
            lir.add(key); store.add(key); S.pop(key, None); S[key] = None
            return False
        if len(store) >= self.c:
            if not Q: self._demote()
            k, _ = Q.popitem(last=False)
            store.discard(k)
            if k in S: self.NR[k] = None
        store.add(key)
        if key in S and self._ok(key):
            del S[key]; S[key] = None; lir.add(key)
            if len(lir) > lc: self._demote()
        else:
            S.pop(key, None)
            S[key] = None; Q[key] = None
        while len(lir) > lc and S:
            self._demote()
        if len(S) > self.maxS:
            NR = self.NR
            while len(S) > self.maxS and NR:
                k, _ = NR.popitem(last=False)
                if k in S and k not in store and k not in lir: del S[k]
        return False


class Freq:
    def __init__(self, capacity, mult, cmax):
        self.cnt = {}; self.n = 0; self.reset = capacity * mult; self.cmax = cmax

    def add(self, k):
        c = self.cnt; v = c.get(k, 0)
        if v < self.cmax: c[k] = v + 1
        self.n += 1
        if self.n >= self.reset:
            self.n = 0
            self.cnt = {k: v >> 1 for k, v in c.items() if v > 1}

    def get(self, k):
        return self.cnt.get(k, 0)




class GAP:
    """Predicts each key's next use as last use + its last reuse gap and evicts the furthest, unless the
    least recently used key is long overdue."""

    def __init__(self, capacity, dflt=4.0, alpha=1.5, hist_mult=4, smooth=0.7):
        self.c = capacity; self.t = 0
        self.dflt = capacity * dflt; self.alpha = alpha; self.sm = smooth
        self.lru = OrderedDict(); self.store = self.lru
        self.last = {}; self.gap = {}
        self.heap = []
        self.hist = OrderedDict(); self.hmax = capacity * hist_mult

    def _push(self, key):
        g = self.gap.get(key)
        p = self.t + (g if g is not None else self.dflt)
        heapq.heappush(self.heap, (-p, self.t, key))

    def access(self, key):
        self.t += 1; t = self.t
        lru, last, gap = self.lru, self.last, self.gap
        if key in lru:
            g = t - last[key]; o = gap.get(key)
            gap[key] = g if o is None else o * self.sm + g * (1 - self.sm)
            last[key] = t; lru.move_to_end(key); self._push(key)
            return True
        h = self.hist.pop(key, None)
        if h is not None:
            g = t - h[0]; o = h[1]
            gap[key] = g if o is None else o * self.sm + g * (1 - self.sm)
        if len(lru) >= self.c:
            o = next(iter(lru)); og = gap.get(o)
            if t - last[o] > self.alpha * (og if og is not None else self.dflt):
                v = o
            else:
                hp = self.heap
                while True:
                    _, s, v = heapq.heappop(hp)
                    if v in lru and last[v] == s: break
            del lru[v]
            self.hist[v] = (last.pop(v), gap.pop(v, None))
            if len(self.hist) > self.hmax: self.hist.popitem(last=False)
        lru[key] = None; last[key] = t; self._push(key)
        if len(self.heap) > 8 * self.c:
            self.heap = [e for e in self.heap if e[2] in lru and last[e[2]] == e[1]]
            heapq.heapify(self.heap)
        return False


class Cache:
    """Simulates LIRS at several settings and two reuse-gap policies on the same requests, and on a miss
    evicts a key that the simulation with the most recent hits is not holding."""

    def __init__(self, capacity, fracs=(0.01, 0.1, 0.3, 0.6), guards=(False, True), ghost_mult=4,
                 fmult=100, cmax=15, win=10, margin=0.05):
        self.c = capacity
        self.freq = Freq(capacity, fmult, cmax)
        self.shadows = []
        for g in guards:
            for f in fracs:
                s = LIRS(capacity, max(1, int(capacity * f)), ghost_mult, self.freq); s.guard = g
                self.shadows.append(s)
        self.shadows.append(GAP(capacity))
        self.shadows.append(GAP(capacity, 64.0, 1.2, 4, 0.85))
        # all LIRS settings share family 0; switching between families costs misses, so needs a margin
        self.fam = [0] * (len(self.shadows) - 2) + [1, 2]
        self.score = [0.0] * len(self.shadows); self.decay = 1 - 1 / (win * capacity)
        self.margin = margin
        self.period = max(1, capacity // 4); self.n = 0
        self.lead = 0; self.store = set(); self.diff = []

    def access(self, key):
        self.freq.add(key)
        sc, d = self.score, self.decay
        for i, s in enumerate(self.shadows):
            sc[i] = sc[i] * d + s.access(key)
        self.n += 1
        if self.n >= self.period:
            self.n = 0
            b = sc.index(max(sc))
            m = self.margin if self.fam[b] != self.fam[self.lead] else 0.0
            if sc[b] > sc[self.lead] * (1 + m): self.lead = b
        st = self.store
        if key in st:
            return True
        if len(st) >= self.c:
            ls = self.shadows[self.lead].store; diff = self.diff
            while True:
                if not diff:
                    diff = self.diff = [k for k in st if k not in ls]
                    if not diff: return False
                k = diff.pop()
                if k in st and k not in ls: break
            st.discard(k)
        st.add(key)
        return False
