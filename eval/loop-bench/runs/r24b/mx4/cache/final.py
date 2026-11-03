"""Cache that runs five eviction policies as shadows and follows whichever has had the most
recent hits: adaptive LIRS (loops), W-TinyLFU and LFU (hot keys), ARC (recency), and an LFU that
drops its counts when the hit rate collapses (shifts in popularity)."""
import heapq
from collections import OrderedDict

class Alirs:
    """LIRS whose resident-HIR share adapts, ARC-style, from ghosts of Q evictions."""
    HIR0 = 0.01; GHOST = 4; GCAP = 1.0; HMAX = 0.5; RD = 0.7

    def _drop(self, k):
        self.store.discard(k); self.ev.append(k)

    def __init__(self, capacity):
        self.cap = capacity
        self.hcap = max(1, int(capacity * self.HIR0))
        self.S = OrderedDict(); self.Q = OrderedDict()
        self.lir = set(); self.store = set()
        self.demoted = set()
        self.G = OrderedDict()
        self.gn = [0, 0]; self.now = 0

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if k in self.lir: break
            del S[k]

    def _demote(self):
        S = self.S
        k = next(iter(S)); self.lir.discard(k); del S[k]
        self.Q[k] = self.now; self.demoted.add(k)
        self._prune()

    def _limit(self):
        S = self.S
        if len(S) > (self.GHOST + 1) * self.cap:
            for k in list(S):
                if len(S) <= self.GHOST * self.cap: break
                if k not in self.store and k not in self.lir:
                    del S[k]

    def _adapt(self, key):
        was, t = self.G.pop(key); gn = self.gn; gn[was] -= 1
        if not was and self.now - t > self.RD * self.cap: return
        hmax = max(1, int(self.cap * self.HMAX))
        if was:
            self.hcap = max(1, self.hcap - max(1, gn[0] // max(1, gn[1])))
        else:
            self.hcap = min(hmax, self.hcap + max(1, gn[1] // max(1, gn[0])))
        while len(self.lir) > self.cap - self.hcap:
            self._demote()

    def access(self, key):
        S, Q = self.S, self.Q
        self.now += 1
        if key in self.lir:
            first = next(iter(S)) == key
            S.move_to_end(key)
            if first: self._prune()
            return True
        if key in self.store:
            if key in S:
                S.move_to_end(key); del Q[key]; self.lir.add(key); self.demoted.discard(key)
                self._demote()
            else:
                S[key] = None; Q.move_to_end(key); Q[key] = self.now
            return True
        if key in self.G: self._adapt(key)
        if len(self.store) >= self.cap:
            if not Q: self._demote()
            k, t = Q.popitem(last=False); self._drop(k)
            was = k in self.demoted
            if was: self.demoted.discard(k)
            self.G[k] = (was, t); self.gn[was] += 1
            if len(self.G) > self.GCAP * self.cap:
                k2, w2 = self.G.popitem(last=False); self.gn[w2[0]] -= 1
        self.store.add(key)
        if len(self.lir) < self.cap - self.hcap:
            self.lir.add(key); S[key] = None; S.move_to_end(key); return False
        if key in S:
            S.move_to_end(key); self.lir.add(key)
            self._demote()
        else:
            S[key] = None; Q[key] = self.now
        self._limit()
        return False


class Wt:
    """W-TinyLFU: LRU window, SLRU main, admission by aged frequency."""
    WIN = 0.01; PROT = 0.8; AGE = 100

    def _drop(self, k):
        self.store.discard(k); self.ev.append(k)

    def __init__(self, capacity):
        self.cap = capacity
        self.wcap = max(1, int(capacity * self.WIN))
        self.mcap = capacity - self.wcap
        self.pcap = int(self.mcap * self.PROT)
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.freq = {}; self.n = 0; self.reset = capacity * self.AGE
        self.store = set()

    def _bump(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.n += 1
        if self.n >= self.reset:
            self.n = 0
            self.freq = {k: v >> 1 for k, v in f.items() if v > 1}

    def access(self, key):
        self._bump(key)
        if key in self.win:
            self.win.move_to_end(key); return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key] = None
            if len(self.prot) > self.pcap:
                k, _ = self.prot.popitem(last=False); self.prob[k] = None
            return True
        self.store.add(key); self.win[key] = None
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if self.mcap <= 0:
                self._drop(cand)
            elif len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = None
            else:
                victim = next(iter(self.prob)) if self.prob else next(iter(self.prot))
                f = self.freq
                if f.get(cand, 0) > f.get(victim, 0):
                    if victim in self.prob: del self.prob[victim]
                    else: del self.prot[victim]
                    self._drop(victim); self.prob[cand] = None
                else:
                    self._drop(cand)
        return False


class Arc:
    def _drop(self, k):
        self.store.discard(k); self.ev.append(k)

    def __init__(self, capacity):
        self.c = capacity; self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = set()

    def _replace(self, inb2):
        if self.t1 and (len(self.t1) > self.p or (inb2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = None
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = None
        self._drop(k)

    def access(self, key):
        c = self.c
        if key in self.t1:
            del self.t1[key]; self.t2[key] = None; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p = min(c, self.p + max(len(self.b2) // max(len(self.b1), 1), 1))
            self._replace(False); del self.b1[key]; self.t2[key] = None; self.store.add(key); return False
        if key in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // max(len(self.b2), 1), 1))
            self._replace(True); del self.b2[key]; self.t2[key] = None; self.store.add(key); return False
        l1 = len(self.t1) + len(self.b1)
        if l1 == c:
            if len(self.t1) < c:
                self.b1.popitem(last=False); self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False); self._drop(k)
        elif l1 < c:
            tot = l1 + len(self.t2) + len(self.b2)
            if tot >= c:
                if tot == 2 * c: self.b2.popitem(last=False)
                self._replace(False)
        self.t1[key] = None; self.store.add(key); return False


class Lfud:
    """LFU with admission; counts are dropped when the short-term hit rate collapses."""
    FAST = 0.5; SLOW = 10.0; DROP = 0.85; AGE = 20; HIST = 16

    def _drop(self, k):
        self.store.discard(k); self.ev.append(k)

    def __init__(self, capacity):
        self.cap = capacity
        self.store = set(); self.f = {}; self.h = []; self.t = 0
        self.ef = self.es = 0.0; self.af = 1.0 / (self.FAST * capacity); self.aslow = 1.0 / (self.SLOW * capacity)
        self.cool = 0; self.n = 0

    def _rebuild(self):
        f = self.f
        self.h = [(f.get(k, 0), self.t, k) for k in self.store]; heapq.heapify(self.h)

    def access(self, key):
        self.t += 1; f = self.f
        v = f.get(key, 0) + 1; f[key] = v
        store = self.store
        hit = key in store
        if hit:
            heapq.heappush(self.h, (v, self.t, key))
        elif len(store) < self.cap:
            store.add(key); heapq.heappush(self.h, (v, self.t, key))
        else:
            h = self.h
            while True:
                pv, pt, k = h[0]
                if k in store and f.get(k, 0) == pv: break
                heapq.heappop(h)
            if v > pv:
                heapq.heappop(h); store.discard(k)
                store.add(key); heapq.heappush(h, (v, self.t, key))
        if len(self.h) > 4 * self.cap + 64: self._rebuild()
        x = 1.0 if hit else 0.0
        self.ef += (x - self.ef) * self.af; self.es += (x - self.es) * self.aslow
        self.cool -= 1; self.n += 1
        if self.cool <= 0 and self.ef < self.DROP * self.es:
            self.f = {}; self.cool = int(self.SLOW * self.cap); self.es = self.ef; self._rebuild()
        elif self.n >= self.AGE * self.cap:
            self.n = 0; self.f = {k: c >> 1 for k, c in f.items() if c > 1}; self._rebuild()
        elif len(f) > self.HIST * self.cap:
            self.f = {k: c for k, c in f.items() if c > 1 or k in store}
        return hit


class Lfu:
    """LFU with admission; counts are dropped when the short-term hit rate collapses."""
    FAST = 0.5; SLOW = 10.0; DROP = -1.0; AGE = 1000; HIST = 64

    def _drop(self, k):
        self.store.discard(k); self.ev.append(k)

    def __init__(self, capacity):
        self.cap = capacity
        self.store = set(); self.f = {}; self.h = []; self.t = 0
        self.ef = self.es = 0.0; self.af = 1.0 / (self.FAST * capacity); self.aslow = 1.0 / (self.SLOW * capacity)
        self.cool = 0; self.n = 0

    def _rebuild(self):
        f = self.f
        self.h = [(f.get(k, 0), self.t, k) for k in self.store]; heapq.heapify(self.h)

    def access(self, key):
        self.t += 1; f = self.f
        v = f.get(key, 0) + 1; f[key] = v
        store = self.store
        hit = key in store
        if hit:
            heapq.heappush(self.h, (v, self.t, key))
        elif len(store) < self.cap:
            store.add(key); heapq.heappush(self.h, (v, self.t, key))
        else:
            h = self.h
            while True:
                pv, pt, k = h[0]
                if k in store and f.get(k, 0) == pv: break
                heapq.heappop(h)
            if v > pv:
                heapq.heappop(h); store.discard(k)
                store.add(key); heapq.heappush(h, (v, self.t, key))
        if len(self.h) > 4 * self.cap + 64: self._rebuild()
        x = 1.0 if hit else 0.0
        self.ef += (x - self.ef) * self.af; self.es += (x - self.es) * self.aslow
        self.cool -= 1; self.n += 1
        if self.cool <= 0 and self.ef < self.DROP * self.es:
            self.f = {}; self.cool = int(self.SLOW * self.cap); self.es = self.ef; self._rebuild()
        elif self.n >= self.AGE * self.cap:
            self.n = 0; self.f = {k: c >> 1 for k, c in f.items() if c > 1}; self._rebuild()
        elif len(f) > self.HIST * self.cap:
            self.f = {k: c for k, c in f.items() if c > 1 or k in store}
        return hit

class Cache:
    """Follows whichever shadow policy has the most recent hits."""
    HALF = 16; MARGIN = 0.05; CHECK = 32

    def __init__(self, capacity):
        self.cap = capacity
        self.ex = [Alirs(capacity), Wt(capacity), Arc(capacity), Lfud(capacity), Lfu(capacity)]
        for e in self.ex: e.ev = []
        self.sc = [0.0] * len(self.ex)
        self.lead = 0
        self.store = set(); self.extras = OrderedDict()
        self.n = 0; self.period = capacity * self.HALF

    def _switch(self, i):
        self.lead = i; ls = self.ex[i].store
        self.extras = OrderedDict((k, None) for k in self.store if k not in ls)

    def access(self, key):
        hit = key in self.store
        sc = self.sc; ex = self.ex
        for i, e in enumerate(ex):
            if e is None: continue
            try:
                if e.access(key): sc[i] += 1
            except Exception:
                ex[i] = None; sc[i] = -1e18
                if i == self.lead:
                    self._switch(max(range(len(sc)), key=lambda j: sc[j]))
        L = ex[self.lead]; ls = L.store; extras = self.extras; store = self.store
        for x in L.ev:
            if x in store: extras[x] = None
        for e in ex:
            if e is not None: e.ev.clear()
        if hit:
            if key in extras and key in ls: del extras[key]
        elif key in ls:
            if len(store) >= self.cap:
                if not extras: self._switch(self.lead)
                if extras:
                    x, _ = extras.popitem(last=False); store.discard(x)
            if len(store) < self.cap: store.add(key)
        elif len(store) < self.cap:
            store.add(key); extras[key] = None
        self.n += 1
        if self.n % self.CHECK == 0:
            if self.n >= self.period:
                self.n = 0
                for i in range(len(sc)): sc[i] *= 0.5
            b = max(range(len(sc)), key=lambda j: sc[j])
            if b != self.lead and sc[b] > sc[self.lead] + self.MARGIN * self.cap:
                self._switch(b)
        return hit
