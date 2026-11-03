from collections import OrderedDict


class Lirs:
    HIST = 3

    def __init__(self, capacity, hf):
        c = self.c = capacity
        self.hc = max(1, int(c * hf))
        self.S = OrderedDict(); self.Q = OrderedDict()
        self.lir = set(); self.store = set()

    def _prune(self):
        S = self.S; lir = self.lir
        while S:
            k = next(iter(S))
            if k in lir: return
            del S[k]

    def set_hc(self, hc):
        self.hc = hc
        lc = self.c - hc
        S, lir = self.S, self.lir
        while len(lir) > lc:
            k = next(iter(S)); lir.discard(k); del S[k]; self.Q[k] = True
            self._prune()

    def access(self, key):
        S, Q, lir, store = self.S, self.Q, self.lir, self.store
        if key in lir:
            S.move_to_end(key); self._prune(); return True
        hit = key in store
        if not hit:
            if len(lir) < self.c - self.hc and len(store) < self.c:
                lir.add(key); store.add(key); S[key] = True; S.move_to_end(key); return False
            if len(store) >= self.c:
                k, _ = Q.popitem(last=False); store.discard(k)
            store.add(key)
        else:
            del Q[key]
        if key in S:
            S.move_to_end(key)
            lir.add(key)
            if len(lir) > self.c - self.hc:
                k = next(iter(S)); lir.discard(k); del S[k]; Q[k] = True
                self._prune()
        else:
            S[key] = True; Q[key] = True
        if len(S) > self.c * self.HIST:
            for k in list(S)[: self.c]:
                if k not in lir and k not in store: del S[k]
            self._prune()
        return hit


class Cache:
    """LIRS whose HIR share is picked by sampled shadow caches with other shares."""

    HFS = (0.01, 0.1, 0.3, 0.6); RATE = 4; PERIOD = 2; DECAY = 0.5

    def __init__(self, capacity):
        self.c = capacity
        self.main = Lirs(capacity, self.HFS[0])
        self.store = self.main.store
        sc = max(4, capacity // self.RATE)
        self.shadows = [Lirs(sc, h) for h in self.HFS]
        self.score = [0.0] * len(self.HFS)
        self.n = 0; self.period = capacity * self.PERIOD

    def access(self, key):
        if (key * 2654435761 >> 7) % self.RATE == 0:
            sc = self.score
            for i, s in enumerate(self.shadows):
                if s.access(key): sc[i] += 1
        self.n += 1
        if self.n >= self.period:
            self.n = 0
            sc = self.score
            best = sc.index(max(sc)) if max(sc) > 0 else 0
            hc = max(1, int(self.c * self.HFS[best]))
            if hc != self.main.hc: self.main.set_hc(hc)
            self.score = [x * self.DECAY for x in sc]
        return self.main.access(key)
