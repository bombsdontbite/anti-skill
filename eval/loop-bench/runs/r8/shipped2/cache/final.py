from collections import OrderedDict


class Lirs:
    def __init__(self, capacity, hcap, hist):
        self.cap = capacity
        self.hcap = hcap
        self.hist = hist
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.lir = set()
        self.store = set()
        self.gate = False
        self.freq = None

    def _ok(self, key):
        if not self.gate: return True
        f = self.freq
        return f.get(key, 0) >= f.get(next(iter(self.S)), 0)

    def _demote_bottom(self):
        S, lir = self.S, self.lir
        k = next(iter(S)); lir.discard(k); del S[k]; self.Q[k] = True
        while S:
            k = next(iter(S))
            if k in lir: break
            del S[k]

    def access(self, key):
        S, Q, lir = self.S, self.Q, self.lir
        if key in lir:
            S.move_to_end(key)
            if next(iter(S)) not in lir:
                while S and next(iter(S)) not in lir: del S[next(iter(S))]
            return True
        lcap = self.cap - self.hcap
        if key in self.store:
            if key in S and self._ok(key):
                del Q[key]; lir.add(key); S.move_to_end(key)
                while len(lir) > lcap: self._demote_bottom()
            else:
                Q.move_to_end(key); S[key] = True; S.move_to_end(key)
            return True
        if len(lir) < lcap and len(self.store) < self.cap:
            lir.add(key); S[key] = True; self.store.add(key); return False
        while len(self.store) >= self.cap:
            if not Q: self._demote_bottom()
            v, _ = Q.popitem(last=False); self.store.discard(v)
        self.store.add(key)
        if key in S and self._ok(key):
            lir.add(key); S.move_to_end(key)
            while len(lir) > lcap: self._demote_bottom()
        else:
            S[key] = True; S.move_to_end(key); Q[key] = True
        if len(S) > self.hist * self.cap:
            for k in list(S):
                if len(S) <= (self.hist - 1) * self.cap: break
                if k not in lir and k not in Q: del S[k]
        return False


class Cache:
    """LIRS whose HIR size follows whichever shadow LIRS (small/large HIR) hit more recently."""

    FRACS = (0.01, 0.1, 0.3)
    HIST = 3.0
    DECAY = 0.9999
    MARGIN = 0.0
    GATED = (0.01,)
    AGE = 30

    def __init__(self, capacity):
        self.sizes = [max(1, int(capacity * f)) for f in self.FRACS]
        self.real = Lirs(capacity, self.sizes[0], self.HIST)
        self.modes = [(h, False) for h in self.sizes]
        self.modes += [(max(1, int(capacity * f)), True) for f in self.GATED]
        self.shadows = []
        for h, g in self.modes:
            sh = Lirs(capacity, h, self.HIST); sh.gate = g; self.shadows.append(sh)
        self.freq = {}
        self.ops = 0
        self.age = self.AGE * capacity
        self.score = [0.0] * len(self.modes)
        self.cur = 0
        self.store = self.real.store

    def access(self, key):
        sc, d = self.score, self.DECAY
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.age:
            self.ops = 0
            self.freq = f = {a: b >> 1 for a, b in f.items() if b > 1}
        for sh in self.shadows: sh.freq = f
        self.real.freq = f
        for i, sh in enumerate(self.shadows):
            sc[i] = sc[i] * d + sh.access(key)
        best = max(range(len(sc)), key=sc.__getitem__)
        if best != self.cur and sc[best] > sc[self.cur] * (1 + self.MARGIN):
            self.cur = best
            self.real.hcap, self.real.gate = self.modes[best]
        return self.real.access(key)

