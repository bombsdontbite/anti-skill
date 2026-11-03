import heapq
from collections import OrderedDict


class Lirs:
    def __init__(self, capacity, hir_frac=0.05, ghost_mult=3.0):
        self.c = capacity
        self.lc = capacity - max(1, int(capacity * hir_frac))
        self.S = OrderedDict(); self.Q = OrderedDict(); self.G = OrderedDict()
        self.lir = set(); self.store = set(); self.ev = []
        self.maxG = max(1, int(capacity * ghost_mult))

    def _prune(self):
        S, lir, G = self.S, self.lir, self.G
        while S:
            k = next(iter(S))
            if k in lir: break
            del S[k]
            if k in G: del G[k]

    def _demote_bottom(self):
        b, _ = self.S.popitem(last=False)
        self.lir.discard(b); self.Q[b] = True
        self._prune()

    def access(self, key):
        S, Q = self.S, self.Q
        if key in self.lir:
            first = next(iter(S)) == key
            S.move_to_end(key)
            if first: self._prune()
            return True
        if key in self.store:
            if key in S:
                S.move_to_end(key); del Q[key]; self.lir.add(key)
                self._demote_bottom()
            else:
                S[key] = True; Q.move_to_end(key)
            return True
        if len(self.lir) < self.lc:
            self.lir.add(key); S[key] = True; S.move_to_end(key); self.store.add(key)
            if key in self.G: del self.G[key]
            return False
        if len(self.store) >= self.c:
            v, _ = Q.popitem(last=False); self.store.discard(v); self.ev.append(v)
            if v in S:
                self.G[v] = True
                if len(self.G) > self.maxG:
                    g, _ = self.G.popitem(last=False); del S[g]
        self.store.add(key)
        if key in self.G:
            del self.G[key]
            S.move_to_end(key); self.lir.add(key)
            self._demote_bottom()
        else:
            S[key] = True; Q[key] = True
        return False


class Lfu:
    def __init__(self, capacity, reset_mult=10):
        self.c = capacity
        self.f = {}; self.store = {}; self.heap = []; self.ev = []
        self.ops = 0
        self.reset = int(capacity * reset_mult)

    def access(self, key):
        f = self.f
        f[key] = f.get(key, 0) + 1
        self.ops += 1
        store = self.store
        if self.ops >= self.reset:
            self.ops = 0
            self.f = f = {a: b * 0.5 for a, b in f.items() if b > 1 or a in store or a == key}
            for k in store: store[k] = f[k]
            self.heap = [(p, k) for k, p in store.items()]
            heapq.heapify(self.heap)
        hit = key in store
        if not hit and len(store) >= self.c:
            h = self.heap
            while True:
                p, k = heapq.heappop(h)
                if store.get(k) == p:
                    del store[k]; self.ev.append(k); break
        p = f[key]
        store[key] = p
        heapq.heappush(self.heap, (p, key))
        return hit


class Arc:
    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = set(); self.ev = []

    def _replace(self, in_b2):
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        self.store.discard(k); self.ev.append(k)

    def access(self, key):
        c = self.c
        if key in self.t1:
            del self.t1[key]; self.t2[key] = True; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p = min(c, self.p + max(len(self.b2) // max(len(self.b1), 1), 1))
            self._replace(False); del self.b1[key]; self.t2[key] = True
        elif key in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // max(len(self.b2), 1), 1))
            self._replace(True); del self.b2[key]; self.t2[key] = True
        else:
            l1 = len(self.t1) + len(self.b1)
            if l1 == c:
                if len(self.t1) < c:
                    self.b1.popitem(last=False); self._replace(False)
                else:
                    k, _ = self.t1.popitem(last=False); self.store.discard(k); self.ev.append(k)
            elif l1 < c and l1 + len(self.t2) + len(self.b2) >= c:
                if l1 + len(self.t2) + len(self.b2) == 2 * c:
                    self.b2.popitem(last=False)
                self._replace(False)
            self.t1[key] = True
        self.store.add(key)
        return False


class Cache:
    """Simulates several policies on key sets only and evicts like whichever had the most recent hits."""

    def __init__(self, capacity, decay_mult=2.0):
        self.c = capacity
        self.sh = [Lirs(capacity), Lfu(capacity), Arc(capacity),
                   Lirs(capacity, 0.01, 32.0), Lfu(capacity, 1000)]
        self.sc = [0.0] * len(self.sh)
        self.d = 1.0 - 1.0 / (capacity * decay_mult)
        self.store = set()

    def access(self, key):
        sc, d = self.sc, self.d
        for i, s in enumerate(self.sh):
            sc[i] = sc[i] * d + s.access(key)
        store = self.store
        if key in store:
            return True
        if len(store) >= self.c:
            w = self.sh[sc.index(max(sc))]
            ev, ws = w.ev, w.store
            while ev:
                v = ev.pop()
                if v in store and v not in ws:
                    store.discard(v); break
            else:
                for v in store:
                    if v not in ws: break
                store.discard(v)
            for s in self.sh:
                if len(s.ev) > 8 * self.c:
                    s.ev = [v for v in s.ev if v in store and v not in s.store]
        store.add(key)
        return False
