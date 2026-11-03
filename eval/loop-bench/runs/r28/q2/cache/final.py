from collections import OrderedDict


class Core:
    """LIRS: inter-reference recency, with a bounded nonresident history."""

    def __init__(self, capacity, hir_frac=0.01, ghost_mult=2.0):
        self.capacity = capacity
        self.hcap = max(1, int(capacity * hir_frac))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict()   # key -> True if LIR
        self.Q = OrderedDict()   # resident HIR
        self.G = OrderedDict()   # nonresident HIR still in S, oldest first
        self.gcap = max(1, int(capacity * ghost_mult))
        self.store = {}
        self.nlir = 0

    def _prune(self):
        S, G = self.S, self.G
        while S:
            k = next(iter(S))
            if S[k]:
                return
            del S[k]
            if k in G:
                del G[k]

    def _demote_bottom(self):
        k, _ = self.S.popitem(last=False)
        self.nlir -= 1
        self.Q[k] = True
        self._prune()

    def _evict(self):
        k, _ = self.Q.popitem(last=False)
        del self.store[k]
        if k in self.S:
            G = self.G
            G[k] = True
            if len(G) > self.gcap:
                g, _ = G.popitem(last=False)
                del self.S[g]

    def access(self, key):
        S, Q, st = self.S, self.Q, self.store
        if key in st:
            if S.get(key):
                first = next(iter(S)) == key
                S.move_to_end(key)
                if first:
                    self._prune()
            elif key in S:
                del S[key]; del Q[key]
                S[key] = True; self.nlir += 1
                self._demote_bottom()
            else:
                S[key] = False
                Q.move_to_end(key)
            return True
        if len(st) >= self.capacity:
            self._evict()
        st[key] = True
        if key in S:
            del S[key]; del self.G[key]
            S[key] = True; self.nlir += 1
            if self.nlir > self.lcap:
                self._demote_bottom()
        elif self.nlir < self.lcap:
            S[key] = True; self.nlir += 1
        else:
            S[key] = False
            Q[key] = True
        return False


class Cache:
    """LIRS whose resident-HIR share grows while a shadow LRU beats a shadow fixed LIRS."""

    def __init__(self, capacity, sample_mult=2, step_frac=0.05, hmax=0.5):
        self.capacity = capacity
        self.main = Core(capacity)
        self.ref = Core(capacity)
        self.store = self.main.store
        self.lru = OrderedDict()
        self.lru_hits = self.ref_hits = self.n = 0
        self.sample = sample_mult * capacity
        self.step = max(1, int(capacity * step_frac))
        self.hmin = self.main.hcap
        self.hmax = max(self.hmin, int(capacity * hmax))

    def _adapt(self):
        m = self.main
        if self.lru_hits > self.ref_hits:
            m.hcap = min(self.hmax, m.hcap + self.step)
        elif self.lru_hits < self.ref_hits:
            m.hcap = max(self.hmin, m.hcap - self.step)
        self.lru_hits = self.ref_hits = self.n = 0
        m.lcap = self.capacity - m.hcap
        while m.nlir > m.lcap:
            m._demote_bottom()

    def access(self, key):
        lru = self.lru
        if key in lru:
            lru.move_to_end(key)
            self.lru_hits += 1
        else:
            lru[key] = True
            if len(lru) > self.capacity:
                lru.popitem(last=False)
        self.ref_hits += self.ref.access(key)
        hit = self.main.access(key)
        self.n += 1
        if self.n >= self.sample:
            self._adapt()
        return hit
