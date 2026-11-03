import random
from collections import OrderedDict, deque

class Lirs:
    """LIRS whose HIR share grows while a shadow LRU out-hits it."""
    def __init__(self, capacity, hfrac=0.01, ghost=3.0, period=0.5, step=0.05, hmax=0.9, margin=0.0):
        c = self.c = capacity
        self.h = max(1.0, c * hfrac)
        self.S = OrderedDict()   # key -> True if LIR
        self.Q = OrderedDict()   # resident HIR
        self.G = OrderedDict()   # non-resident HIR still in S
        self.nlir = 0
        self.gmax = int(c * ghost)
        self.period = int(c * period); self.t = 0; self.hits = 0; self.prev = -1
        self.step = c * step; self.hmax = c * hmax
        self.store = set(); self.ev = []
        self.lru = OrderedDict(); self.lhits = 0; self.margin = margin
        self.hmin = max(1.0, c * hfrac)

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if S[k]: return
            del S[k]; self.G.pop(k, None)

    def _demote(self):
        S = self.S; lcap = self.c - int(self.h)
        while self.nlir > lcap:
            k = next(iter(S)); del S[k]
            self.nlir -= 1; self.Q[k] = True
            self._prune()

    def access(self, key):
        self.t += 1
        lru = self.lru
        if key in lru:
            lru.move_to_end(key); self.lhits += 1
        else:
            lru[key] = True
            if len(lru) > self.c: lru.popitem(last=False)
        if self.t >= self.period:
            if self.lhits > self.hits * (1 + self.margin): self.h = min(self.hmax, self.h + self.step)
            else: self.h = max(self.hmin, self.h - self.step)
            self.hits = 0; self.lhits = 0; self.t = 0
        S = self.S; Q = self.Q; store = self.store
        if key in store:
            self.hits += 1
            if key in Q:
                if key in S:
                    S[key] = True; S.move_to_end(key); del Q[key]; self.nlir += 1
                    self._demote()
                else:
                    S[key] = False; Q.move_to_end(key)
            else:
                S.move_to_end(key); self._prune()
            return True
        if len(store) >= self.c:
            if Q:
                v, _ = Q.popitem(last=False)
                if v in S: self.G[v] = True
            else:
                v = next(iter(S)); del S[v]; self.nlir -= 1; self._prune()
            store.discard(v); self.ev.append(v)
        store.add(key)
        self.G.pop(key, None)
        if key in S or self.nlir < self.c - int(self.h):
            S.pop(key, None); S[key] = True; self.nlir += 1
            self._demote()
        else:
            S[key] = False; Q[key] = True
        G = self.G
        while len(G) > self.gmax:
            g, _ = G.popitem(last=False)
            if g in S: del S[g]
        return False

class Tlfu:
    """W-TinyLFU: small LRU window, SLRU main, frequency-sketch admission."""
    def __init__(self, capacity, wfrac=0.01, age=10):
        self.c = capacity
        self.wcap = max(1, int(capacity * wfrac))
        mcap = capacity - self.wcap
        self.pcap = int(mcap * 0.8)
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.f = {}
        self.ops = 0
        self.reset = capacity * age
        self.store = set(); self.ev = []

    def _inc(self, k):
        f = self.f
        f[k] = f.get(k, 0) + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.f = {a: b >> 1 for a, b in f.items() if b > 1}

    def access(self, key):
        self._inc(key)
        if key in self.win:
            self.win.move_to_end(key); return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key] = True
            if len(self.prot) > self.pcap:
                k, _ = self.prot.popitem(last=False); self.prob[k] = True
            return True
        self.win[key] = True; self.store.add(key)
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.c - self.wcap:
                self.prob[cand] = True
            elif not self.prob and not self.prot:
                self.store.discard(cand); self.ev.append(cand)
            else:
                victim = next(iter(self.prob)) if self.prob else next(iter(self.prot))
                f = self.f
                if f.get(cand, 0) > f.get(victim, 0):
                    if victim in self.prob: del self.prob[victim]
                    else: del self.prot[victim]
                    self.store.discard(victim); self.ev.append(victim); self.prob[cand] = True
                else:
                    self.store.discard(cand); self.ev.append(cand)
        return False


class S3:
    """S3-FIFO."""
    def __init__(self, capacity, sfrac=0.1):
        self.c = capacity; self.scap = max(1, int(capacity * sfrac))
        self.S = deque(); self.M = deque(); self.fr = {}; self.G = OrderedDict()
        self.ns = 0
        self.store = set(); self.ev = []

    def _out(self, k):
        del self.fr[k]; self.store.discard(k); self.ev.append(k)

    def _evict(self):
        S = self.S; M = self.M; fr = self.fr
        if self.ns >= self.scap or not M:
            while S:
                k = S.popleft(); self.ns -= 1
                if fr[k] > 0:
                    fr[k] = 0; M.append(k)
                    if len(M) > self.c - self.scap: self._evict_m()
                    if len(self.store) < self.c: return
                else:
                    self._out(k); self.G[k] = True
                    if len(self.G) > self.c: self.G.popitem(last=False)
                    return
        self._evict_m()

    def _evict_m(self):
        M = self.M; fr = self.fr
        while True:
            k = M.popleft()
            if fr[k] > 0: fr[k] -= 1; M.append(k)
            else: self._out(k); return

    def access(self, key):
        if key in self.store:
            f = self.fr[key]
            if f < 3: self.fr[key] = f + 1
            return True
        while len(self.store) >= self.c: self._evict()
        self.fr[key] = 0; self.store.add(key)
        if key in self.G: del self.G[key]; self.M.append(key)
        else: self.S.append(key); self.ns += 1
        return False


class Pred:
    """Sampled eviction of the key whose next access, from its smoothed reuse gap, is furthest off."""
    def __init__(self, capacity, alpha=0.5, newpen=2.0, hist=8.0, sample=32, od=1.0):
        self.c = capacity; self.al = alpha; self.np = newpen * capacity; self.k = sample; self.od = od
        self.last = {}; self.gap = {}; self.t = 0
        self.keys = []; self.idx = {}; self.rng = random.Random(3)
        self.hist = int(hist * capacity)
        self.store = self.idx; self.ev = []

    def access(self, key):
        t = self.t = self.t + 1
        last = self.last; gap = self.gap
        if key in last:
            g = t - last[key]; og = gap.get(key)
            gap[key] = g if og is None else og + self.al * (g - og)
        last[key] = t
        if key in self.idx: return True
        keys = self.keys
        if len(keys) >= self.c:
            r = self.rng; best = None; bs = -1.0; npen = self.np; od = self.od
            for _ in range(self.k):
                x = keys[int(r.random() * len(keys))]
                a = t - last[x]; g = gap.get(x, npen)
                s = g - a if a < g else od * a
                if s > bs: bs = s; best = x
            i = self.idx.pop(best); lk = keys.pop()
            if lk != best: keys[i] = lk; self.idx[lk] = i
            self.ev.append(best)
        self.idx[key] = len(keys); keys.append(key)
        if t % self.hist == 0:
            lim = t - self.hist
            for k in [k for k, v in last.items() if v < lim and k not in self.idx]:
                del last[k]; gap.pop(k, None)
        return False


class Cache:
    """Runs LIRS, W-TinyLFU and S3-FIFO in shadow and follows whichever has hit most lately.
    Keys the leader drops stay cached as spares until their slot is needed."""
    def __init__(self, capacity, horizon=80.0, margin=0.0, ages=(10, 40), s3=1, lazy=1, pred=((2.0, 10.0),), pa=0.15, ps=32):
        self.c = capacity
        self.E = ([Lirs(capacity)] if capacity > 1 else []) + [Tlfu(capacity, age=a) for a in ages]
        if s3: self.E.append(S3(capacity))
        for npen, od in pred: self.E.append(Pred(capacity, newpen=npen, od=od, alpha=pa, sample=ps))
        self.sc = [0.0] * len(self.E); self.d = 1.0 - 1.0 / (capacity * horizon); self.m = margin
        self.a = 0; self.lazy = lazy
        self.spare = OrderedDict()
        self.store = set()

    def access(self, key):
        st = self.store
        hit = key in st
        sc = self.sc; d = self.d
        for i, e in enumerate(self.E):
            e.ev.clear()
            sc[i] = sc[i] * d + e.access(key)
        a = self.a; o = 0
        for i in range(1, len(sc)):
            if sc[i] > sc[o]: o = i
        spare = self.spare
        if o != a and sc[o] > sc[a] * (1 + self.m) + 1:
            self.a = a = o
            es = self.E[a].store
            for k in st:
                if k not in es and k not in spare: spare[k] = True
            for k in list(spare):
                if k in es: del spare[k]
        else:
            for k in self.E[a].ev:
                if k in st: spare[k] = True
        es = self.E[a].store
        if key in es:
            spare.pop(key, None)
            if not hit: st.add(key)
        elif hit:
            spare.move_to_end(key)
        if not self.lazy:
            while spare: st.discard(spare.popitem(last=False)[0])
        while len(st) > self.c:
            st.discard(spare.popitem(last=False)[0])
        return hit
