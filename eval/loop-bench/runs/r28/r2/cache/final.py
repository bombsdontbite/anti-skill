from collections import OrderedDict


class _Lirs:
    """LIRS whose resident-HIR share (hcap) may change between accesses."""

    def __init__(self, capacity, hcap, ghost_mult):
        self.capacity = capacity
        self.hcap = hcap
        self.S = OrderedDict()   # key -> True if LIR
        self.Q = OrderedDict()   # resident HIR
        self.res = {}
        self.nlir = 0
        self.slimit = ghost_mult * capacity

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if S[k]:
                break
            del S[k]

    def _demote(self):
        S = self.S
        k = next(iter(S))
        del S[k]
        self.Q[k] = True
        self.nlir -= 1
        self._prune()

    def _trim(self):
        S = self.S
        if len(S) > self.slimit:
            res = self.res
            for k in list(S)[:len(S) - self.slimit + self.capacity]:
                if not S[k] and k not in res:
                    del S[k]

    def access(self, key):
        S, Q = self.S, self.Q
        lcap = self.capacity - self.hcap
        if key in self.res:
            if S.get(key):
                first = next(iter(S)) == key
                S.move_to_end(key)
                if first:
                    self._prune()
            elif key in S:
                del Q[key]
                S.move_to_end(key)
                S[key] = True
                self.nlir += 1
                while self.nlir > lcap:
                    self._demote()
            else:
                S[key] = False
                Q.move_to_end(key)
            return True, None
        evicted = None
        if len(self.res) >= self.capacity:
            if not Q:
                self._demote()
            evicted, _ = Q.popitem(last=False)
            del self.res[evicted]
        self.res[key] = True
        if key in S or self.nlir < lcap:
            S[key] = True
            S.move_to_end(key)
            self.nlir += 1
            while self.nlir > lcap:
                self._demote()
        else:
            S[key] = False
            Q[key] = True
        self._trim()
        return False, evicted


class Cache:
    """LIRS whose HIR share follows virtual small-HIR LIRS and LRU caches."""

    def __init__(self, capacity, hir_frac=0.01, ghost_mult=3, period_mult=1,
                 step_frac=0.25, alpha=0.5):
        self.capacity = capacity
        self.hmin = max(1, int(capacity * hir_frac))
        self.hmax = capacity - 1
        self.real = _Lirs(capacity, self.hmin, ghost_mult)
        self.store = self.real.res
        self.small = _Lirs(capacity, self.hmin, ghost_mult)
        self.lru = OrderedDict()
        self.hs = self.hl = self.n = 0
        self.es = self.el = 0.0
        self.alpha = alpha
        self.period = max(1, int(period_mult * capacity))
        self.step = max(1, int(capacity * step_frac))

    def _shadow(self, key):
        if self.small.access(key)[0]:
            self.hs += 1
        lru = self.lru
        if key in lru:
            lru.move_to_end(key)
            self.hl += 1
        else:
            lru[key] = True
            if len(lru) > self.capacity:
                lru.popitem(last=False)
        self.n += 1
        if self.n >= self.period:
            a = self.alpha
            self.es = a * self.es + (1 - a) * self.hs / self.n
            self.el = a * self.el + (1 - a) * self.hl / self.n
            self.hs = self.hl = self.n = 0
            r = self.real
            if self.el > self.es:
                r.hcap = min(self.hmax, r.hcap + self.step)
            else:
                r.hcap = max(self.hmin, r.hcap - self.step)

    def access(self, key):
        self._shadow(key)
        return self.real.access(key)[0]
