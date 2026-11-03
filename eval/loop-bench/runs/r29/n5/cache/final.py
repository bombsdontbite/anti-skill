from collections import OrderedDict


class _LIRS:
    """LIRS with a resizable LIR set."""

    def __init__(self, capacity, hir, hist=3):
        self.c = capacity
        self.lmax = capacity - max(1, int(capacity * hir))
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.lir = set()
        self.keys = set()
        self.smax = hist * capacity

    def resize(self, hir, hist):
        self.smax = hist * self.c
        self.lmax = self.c - max(1, int(self.c * hir))
        S, lir = self.S, self.lir
        while len(lir) > self.lmax:
            k = next(iter(S)); lir.discard(k); del S[k]; self.Q[k] = None
            self._prune()

    def _prune(self):
        S, lir = self.S, self.lir
        while S:
            k = next(iter(S))
            if k in lir: return
            del S[k]

    def _demote(self):
        S = self.S
        k = next(iter(S)); self.lir.discard(k); del S[k]; self.Q[k] = None
        self._prune()

    def access(self, key):
        S, Q, lir, keys = self.S, self.Q, self.lir, self.keys
        if key in lir:
            first = next(iter(S)) == key
            S.move_to_end(key)
            if first: self._prune()
            return True
        if key in keys:
            if key in S:
                del Q[key]; lir.add(key); S.move_to_end(key)
                if len(lir) > self.lmax: self._demote()
            else:
                S[key] = None; Q.move_to_end(key)
            return True
        if len(keys) >= self.c:
            if Q:
                k, _ = Q.popitem(last=False)
            else:
                k = next(iter(S)); lir.discard(k); del S[k]; self._prune()
            keys.discard(k)
        keys.add(key)
        if len(lir) < self.lmax:
            lir.add(key); S[key] = None; S.move_to_end(key)
        elif key in S:
            lir.add(key); S.move_to_end(key)
            self._demote()
        else:
            S[key] = None; Q[key] = None
            if len(S) > self.smax: self._trim()
        return False

    def _trim(self):
        S, lir, Q = self.S, self.lir, self.Q
        n = len(S) - self.smax + self.c
        for k in [k for k in S if k not in lir and k not in Q][:n]:
            del S[k]


class Cache:
    """LIRS whose HIR share and history length follow the best of several sampled shadow simulations."""

    HIRS = (0.01, 0.03, 0.1, 0.25, 0.5, 0.8)
    HISTS = (2, 3, 6)
    DECAY = 0.999

    def __init__(self, capacity):
        self.c = capacity
        self.rate = max(1, min(8, capacity // 48))
        mc = max(4, capacity // self.rate)
        self.cfg = [(h, n) for h in self.HIRS for n in self.HISTS]
        self.sims = [_LIRS(mc, h, n) for h, n in self.cfg]
        self.score = [0.0] * len(self.cfg)
        self.cur = 1
        self.main = _LIRS(capacity, *self.cfg[1])
        self.store = self.main.keys
        self.tick = 0

    def access(self, key):
        if (key * 2654435761 >> 7) % self.rate == 0:
            sc = self.score; d = self.DECAY
            for i, s in enumerate(self.sims):
                sc[i] = sc[i] * d + s.access(key)
            self.tick += 1
            if self.tick >= 64:
                self.tick = 0
                best = sc.index(max(sc))
                if best != self.cur:
                    self.cur = best
                    self.main.resize(*self.cfg[best])
        return self.main.access(key)
