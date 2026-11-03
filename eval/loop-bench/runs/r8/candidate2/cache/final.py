from collections import OrderedDict


class FixedLIRS:
    """Fixed LIRS, used as a key-only shadow."""

    def __init__(self, capacity, hfrac=0.01):
        self.cap = capacity
        self.hcap = max(1, int(capacity * hfrac))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict()  # key -> True; recency stack
        self.Q = OrderedDict()  # resident HIR
        self.lir = set()
        self.store = set()
        self.nonres = 0

    def _prune(self):
        while self.S:
            k = next(iter(self.S))
            if k in self.lir: return
            del self.S[k]

    def access(self, key):
        S, Q, lir = self.S, self.Q, self.lir
        if key in lir:
            S.move_to_end(key); self._prune(); return True
        if key in Q:
            if key in S:
                del Q[key]; S.move_to_end(key); lir.add(key)
                k = next(iter(S)); lir.discard(k); del S[k]; Q[k] = True
                self._prune()
            else:
                Q.move_to_end(key); S[key] = True
            return True
        # miss
        if len(lir) < self.lcap:
            lir.add(key); S[key] = True; S.move_to_end(key); self.store.add(key); return False
        if len(self.store) >= self.cap:
            k, _ = Q.popitem(last=False); self.store.discard(k)
        self.store.add(key)
        if key in S:
            S.move_to_end(key); lir.add(key)
            k = next(iter(S)); lir.discard(k); del S[k]; Q[k] = True
            self._prune()
        else:
            S[key] = True; Q[key] = True
        if len(S) > 6 * self.cap:
            for k in list(S):
                if len(S) <= 5 * self.cap: break
                if k not in lir and k not in Q: del S[k]
        return False


class Cache:
    """LIRS whose resident-HIR share adapts to hits in two ghost lists sized like ARC's."""

    def __init__(self, capacity, hfrac=0.01, smul=4, up=4, down=1):
        self.cap = capacity
        self.hcap = max(1, int(capacity * hfrac))
        self.hmin = self.hcap
        self.hmax = capacity - max(1, capacity // 10)
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.lir = set()
        self.demoted = set()
        self.GH = OrderedDict()  # evicted HIR keys, window ~ hcap
        self.GL = OrderedDict()  # evicted demoted-LIR keys, window ~ lcap
        self.store = set()
        self.smax = smul * capacity
        self.up, self.down = up, down
        self.shadow = FixedLIRS(capacity)
        self.lru = OrderedDict()
        self.score = 0.0
        self.n = 0
        self.win = 5 * capacity

    def _prune(self):
        S, lir = self.S, self.lir
        while S:
            k = next(iter(S))
            if k in lir: return
            del S[k]

    def _demote(self):
        k, _ = self.S.popitem(last=False)
        self.lir.discard(k); self.Q[k] = True; self.demoted.add(k)
        self._prune()

    def _promote(self, key):
        self.S.move_to_end(key); self.lir.add(key); self.demoted.discard(key)
        while len(self.lir) > self.cap - self.hcap: self._demote()

    def access(self, key):
        lru = self.lru
        if key in lru:
            lru.move_to_end(key); self.score += 1
        else:
            lru[key] = True
            if len(lru) > self.cap: lru.popitem(last=False)
        if self.shadow.access(key): self.score -= 1
        self.n += 1
        if self.n >= self.win:
            self.n = 0
            if self.score <= 0: self.hcap = max(self.hmin, self.hcap // 2)
            self.score *= 0.5
        return self._access(key)

    def _access(self, key):
        S, Q, lir = self.S, self.Q, self.lir
        if key in lir:
            S.move_to_end(key); self._prune(); return True
        if key in Q:
            if key in S:
                del Q[key]; self._promote(key)
            else:
                Q.move_to_end(key); S[key] = True
            return True
        if key in self.GH:
            del self.GH[key]
            if self.score > 0: self.hcap = min(self.hmax, self.hcap + max(self.up, min(4, len(self.GL) // max(1, len(self.GH)))))
        elif key in self.GL:
            del self.GL[key]; self.hcap = max(self.hmin, self.hcap - max(1, len(self.GH) // max(1, len(self.GL))))
        if len(lir) < self.cap - self.hcap and len(self.store) < self.cap:
            lir.add(key); S[key] = True; S.move_to_end(key); self.store.add(key); return False
        if len(self.store) >= self.cap:
            if not Q: self._demote()
            k, _ = Q.popitem(last=False); self.store.discard(k)
            if k in self.demoted:
                self.demoted.discard(k); G = self.GL; lim = self.cap - self.hcap
            else:
                G = self.GH; lim = self.hcap
            G[k] = True
            while len(G) > lim: G.popitem(last=False)
        self.store.add(key)
        if key in S:
            self._promote(key)
        else:
            S[key] = True; Q[key] = True
        if len(S) > self.smax:
            for k in list(S):
                if len(S) <= self.smax - self.cap: break
                if k not in lir and k not in Q: del S[k]
        return False
