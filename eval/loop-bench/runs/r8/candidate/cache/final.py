from collections import OrderedDict


class Cache:
    """LIRS whose resident-HIR share grows while a shadow LRU of the same size out-hits it."""

    def __init__(self, capacity, hfrac=0.01, smul=2, period_mul=2, step_frac=0.05, hmax=0.9):
        self.cap = capacity
        self.smul = smul
        self.hcap = max(1, int(capacity * hfrac))
        self.hmin = self.hcap; self.hmax = max(self.hmin, int(capacity * hmax))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict(); self.Q = OrderedDict()
        self.lir = set(); self.store = set()
        self.period = capacity * period_mul; self.t = 0; self.hits = 0
        self.step = max(1, int(capacity * step_frac))
        self.lru = OrderedDict(); self.lhits = 0

    def _prune(self):
        S, lir = self.S, self.lir
        while S:
            k = next(iter(S))
            if k in lir: return
            del S[k]

    def _demote(self):
        S = self.S
        k = next(iter(S)); self.lir.discard(k); del S[k]; self.Q[k] = True; self._prune()

    def _climb(self):
        d = self.step if self.lhits > self.hits else -self.step if self.lhits < self.hits else 0
        self.hits = 0; self.lhits = 0; self.t = 0
        self.hcap = min(self.hmax, max(self.hmin, self.hcap + d))
        self.lcap = self.cap - self.hcap
        while len(self.lir) > self.lcap: self._demote()

    def access(self, key):
        hit = self._access(key)
        lru = self.lru
        if key in lru:
            lru.move_to_end(key); self.lhits += 1
        else:
            lru[key] = True
            if len(lru) > self.cap: lru.popitem(last=False)
        self.t += 1
        if hit: self.hits += 1
        if self.t >= self.period: self._climb()
        return hit

    def _access(self, key):
        S, Q, lir = self.S, self.Q, self.lir
        if key in lir:
            S.move_to_end(key); self._prune(); return True
        if key in self.store:
            if key in S:
                S.move_to_end(key); del Q[key]; lir.add(key)
                if len(lir) > self.lcap: self._demote()
            else:
                S[key] = True; Q.move_to_end(key)
            return True
        if len(lir) < self.lcap and not Q and len(self.store) < self.cap:
            lir.add(key); S[key] = True; self.store.add(key); return False
        while len(self.store) >= self.cap:
            k, _ = Q.popitem(last=False); self.store.discard(k)
        self.store.add(key)
        if key in S:
            S.move_to_end(key); lir.add(key)
            if len(lir) > self.lcap: self._demote()
        else:
            S[key] = True; Q[key] = True
        lim = self.smul * self.cap
        if len(S) > lim + self.cap:
            for k in list(S):
                if len(S) <= lim: break
                if k not in lir and k not in Q: del S[k]
        return False
