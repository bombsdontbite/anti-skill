from collections import OrderedDict


class Lirs:
    """LIRS with a resizable resident-HIR share."""

    def __init__(self, capacity, hcap, ghost_mult, T=0):
        self.capacity = capacity
        self.hcap = hcap
        self.lcap = capacity - hcap
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.lir = set()
        self.store = set()
        self.gmax = capacity * ghost_mult
        self.nghost = 0
        self.T = T
        self.ref = {}

    def resize(self, hcap):
        self.hcap = hcap
        self.lcap = self.capacity - hcap
        while len(self.lir) > self.lcap:
            self._demote_bottom()

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if k in self.lir:
                break
            del S[k]
            if k not in self.store:
                self.nghost -= 1

    def _demote_bottom(self):
        S = self.S
        if self.T:
            ref = self.ref
            for _ in range(8):
                k = next(iter(S))
                if ref.get(k, 0) < self.T:
                    break
                ref[k] = 0
                S.move_to_end(k)
                self._prune()
        k, _ = S.popitem(last=False)
        self.ref.pop(k, None)
        self.lir.discard(k)
        self.Q[k] = True
        self._prune()

    def _evict(self):
        k, _ = self.Q.popitem(last=False)
        self.store.discard(k)
        if k in self.S:
            self.nghost += 1

    def access(self, x):
        S = self.S
        if x in self.lir:
            if self.T:
                self.ref[x] = self.ref.get(x, 0) + 1
            first = next(iter(S)) == x
            S.move_to_end(x)
            if first:
                self._prune()
            return True
        if x in self.store:
            if x in S:
                S.move_to_end(x)
                del self.Q[x]
                self.lir.add(x)
                self._demote_bottom()
            else:
                S[x] = True
                self.Q.move_to_end(x)
            return True
        if len(self.store) >= self.capacity:
            self._evict()
        self.store.add(x)
        if len(self.lir) < self.lcap:
            if x in S:
                self.nghost -= 1
            S[x] = True
            S.move_to_end(x)
            self.lir.add(x)
            return False
        if x in S:
            self.nghost -= 1
            S.move_to_end(x)
            self.lir.add(x)
            self._demote_bottom()
        else:
            S[x] = True
            self.Q[x] = True
        if self.nghost > self.gmax:
            for k in list(S):
                if self.nghost <= self.gmax // 2:
                    break
                if k not in self.store:
                    del S[k]
                    self.nghost -= 1
            self._prune()
        return False


class Cache:
    """LIRS whose settings follow the best of several shadow LIRS caches."""

    def __init__(self, capacity, fracs=(0.01, 0.3), ghosts=(3, 10), Ts=(0, 1), SM=2, DEC=0.5):
        self.cfg = [(max(1, int(capacity * f)), g, T) for T in Ts for g in ghosts for f in fracs]
        self.real = Lirs(capacity, *self.cfg[0])
        self.store = self.real.store
        self.shadows = [Lirs(capacity, *c) for c in self.cfg]
        self.score = [0.0] * len(self.cfg)
        self.cur = 0
        self.sample = capacity * SM
        self.n = 0
        self.dec = DEC

    def access(self, x):
        sc = self.score
        for i, s in enumerate(self.shadows):
            if s.access(x):
                sc[i] += 1
        self.n += 1
        if self.n >= self.sample:
            self.n = 0
            best = max(range(len(sc)), key=lambda i: (sc[i], -i))
            if best != self.cur:
                self.cur = best
                h, g, T = self.cfg[best]
                self.real.T = T
                self.real.gmax = self.real.capacity * g
                self.real.resize(h)
            for i in range(len(sc)):
                sc[i] *= self.dec
        return self.real.access(x)
