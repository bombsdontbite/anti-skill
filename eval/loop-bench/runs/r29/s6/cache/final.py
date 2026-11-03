from collections import OrderedDict

LIR, HIR, NR = 0, 1, 2


class Cache:
    """LIRS whose LIR share adapts ARC-style on misses to recently evicted keys."""

    def __init__(self, capacity, hfrac=0.01, nrmax=2.0, gfrac=0.5, up=4.0, down=0.5, fthr=2, reset=10):
        self.cap = capacity
        self.lcap = capacity - max(1, int(capacity * hfrac))
        self.S = OrderedDict(); self.Q = OrderedDict(); self.st = {}
        self.store = set(); self.nlir = 0; self.nnr = 0; self.nrmax = int(capacity * nrmax)
        self.G = OrderedDict(); self.gcap = int(capacity * gfrac); self.up = up; self.down = down
        self.demoted = set(); self.target = float(self.lcap)
        self.freq = {}; self.fthr = fthr; self.ops = 0; self.reset = capacity * reset

    def _prune(self):
        S, st = self.S, self.st
        while S:
            k = next(iter(S))
            if st[k] == LIR:
                return
            del S[k]
            if st[k] == NR:
                del st[k]; self.nnr -= 1

    def _demote_bottom(self):
        S = self.S
        k, _ = S.popitem(last=False)
        self.st[k] = HIR; self.Q[k] = 1; self.demoted.add(k)
        self._prune()

    def access(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = {a: b >> 1 for a, b in f.items() if b > 1}
        S, Q, st = self.S, self.Q, self.st
        s = st.get(key)
        if s == LIR:
            S.move_to_end(key)
            self._prune()
            return True
        if s == HIR:
            if key in S:
                S.move_to_end(key); del Q[key]; st[key] = LIR; self.demoted.discard(key)
                self._demote_bottom()
            else:
                S[key] = 1; Q.move_to_end(key)
            return True
        if len(self.store) >= self.cap:
            v, _ = Q.popitem(last=False); self.store.discard(v)
            self.G[v] = v in self.demoted; self.demoted.discard(v)
            if len(self.G) > self.gcap:
                self.G.popitem(last=False)
            if v in S:
                st[v] = NR; self.nnr += 1
            else:
                del st[v]
        self.store.add(key)
        g = self.G.pop(key, None)
        if g is not None:
            if g:
                self.target = min(self.cap - 1.0, self.target + self.up)
            # frequent keys returning from the ghost are loops longer than the cache: keep the LIR share
            elif self.freq.get(key, 0) <= self.fthr:
                self.target = max(1.0, self.target - self.down)
            self.lcap = int(self.target)
            while self.nlir > self.lcap:
                self.nlir -= 1
                self._demote_bottom()
            s = st.get(key)
        if self.nlir < self.lcap:
            if s == NR:
                self.nnr -= 1
            self.demoted.discard(key)
            st[key] = LIR; S[key] = 1; S.move_to_end(key); self.nlir += 1
        elif s == NR:
            self.nnr -= 1
            self.demoted.discard(key)
            st[key] = LIR; S.move_to_end(key)
            self._demote_bottom()
        else:
            st[key] = HIR; S[key] = 1; Q[key] = 1
        if self.nnr > self.nrmax:
            for k in [k for k in S if st[k] == NR][: self.nnr - self.nrmax // 2]:
                del S[k]; del st[k]; self.nnr -= 1
        return False
