from collections import OrderedDict


class _Lirs:
    def __init__(self, capacity, hir):
        self.capacity = capacity
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.lir = set()
        self.store = {}
        self.set_hir(hir)

    def set_hir(self, hir):
        self.lcap = self.capacity - max(1, int(self.capacity * hir))
        while len(self.lir) > self.lcap:
            self._demote()

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if k in self.lir:
                return
            del S[k]

    def _demote(self):
        S = self.S
        k = next(iter(S))
        del S[k]
        self.lir.discard(k)
        self.Q[k] = True
        self._prune()

    def access(self, key):
        S, Q, lir, store = self.S, self.Q, self.lir, self.store
        if key in lir:
            S.move_to_end(key)
            self._prune()
            return True
        if key in store:
            if key in S:
                S.move_to_end(key)
                del Q[key]
                lir.add(key)
                while len(lir) > self.lcap:
                    self._demote()
            else:
                S[key] = True
                Q.move_to_end(key)
            return True
        if len(lir) < self.lcap and len(store) < self.capacity:
            lir.add(key)
            S[key] = True
            store[key] = True
            return False
        if len(store) >= self.capacity:
            if Q:
                k, _ = Q.popitem(last=False)
            else:
                self._demote()
                k, _ = Q.popitem(last=False)
            del store[k]
        store[key] = True
        if key in S:
            S.move_to_end(key)
            lir.add(key)
            while len(lir) > self.lcap:
                self._demote()
        else:
            S[key] = True
            Q[key] = True
        if len(S) > 6 * self.capacity:
            for k in list(S)[: self.capacity]:
                if k not in lir:
                    del S[k]
        return False


class _Core:
    def __init__(self, capacity, wfrac, protf, owner, fi=0):
        self.capacity = capacity
        self.store = {}
        self.window = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.wcap = max(1, int(capacity * wfrac))
        self.protf = protf
        self.owner = owner
        self.fi = fi

    def access(self, key):
        if key in self.window:
            self.window.move_to_end(key)
            return True
        if key in self.prot:
            self.prot.move_to_end(key)
            return True
        if key in self.prob:
            del self.prob[key]
            self.prot[key] = True
            pcap = int((self.capacity - self.wcap) * self.protf)
            while len(self.prot) > pcap:
                k, _ = self.prot.popitem(last=False)
                self.prob[k] = True
            return True
        f = self.owner.freqs[self.fi]
        cap = self.capacity
        store = self.store
        self.window[key] = True
        store[key] = True
        while len(store) > cap:
            if len(self.window) > self.wcap:
                cand, _ = self.window.popitem(last=False)
                main = self.prob if self.prob else self.prot
                if not main:
                    del store[cand]
                    continue
                victim = next(iter(main))
                if f.get(cand, 0) > f.get(victim, 0):
                    del main[victim]
                    del store[victim]
                    self.prob[cand] = True
                else:
                    del store[cand]
            else:
                main = self.prob if self.prob else self.prot
                k, _ = main.popitem(last=False)
                del store[k]
        while len(self.window) > self.wcap and len(store) <= cap:
            cand, _ = self.window.popitem(last=False)
            self.prob[cand] = True
        return False


class Cache:
    """Switches between adaptive LIRS and W-TinyLFU configurations by shadow simulation."""

    def __init__(self, capacity, hirs=(0.01, 0.05, 0.2, 0.5, 0.9), fracs=(0.01, 0.2, 0.99),
                 resets=(3, 30), decay=0.999, every=0.25, margin=0.02, fmargin=0.05):
        self.capacity = capacity
        self.freqs = [{} for _ in resets]
        self.ops = [0] * len(resets)
        self.resets = [r * capacity for r in resets]
        self.conf = [("l", h, 0) for h in hirs] + [("t", w, j) for j in range(len(resets)) for w in fracs]
        self.shadows = []
        for kind, x, j in self.conf:
            if kind == "l":
                self.shadows.append(_Lirs(capacity, x))
            else:
                self.shadows.append(_Core(capacity, x, 0.5, self, j))
        self.scores = [0.0] * len(self.conf)
        self.real = _Lirs(capacity, hirs[0])
        self.store = self.real.store
        self.cur = 0
        self.decay = decay
        self.every = max(1, int(every * capacity))
        self.n = 0
        self.margin = margin
        self.fmargin = fmargin

    def _switch(self, best):
        kind, x, j = self.conf[best]
        old = self.real
        if kind == self.conf[self.cur][0]:
            if kind == "l":
                old.set_hir(x)
            else:
                old.wcap = max(1, int(self.capacity * x))
                old.fi = j
            self.cur = best
            return
        if kind == "t":
            new = _Core(self.capacity, x, 0.5, self, j)
            order = [k for k in old.S if k in old.store] + [k for k in old.Q if k not in old.S]
            seen = set()
            for k in order:
                if k not in seen:
                    seen.add(k)
                    new.prob[k] = True
        else:
            new = _Lirs(self.capacity, x)
            order = list(old.prob) + list(old.prot) + list(old.window)
            n = len(order)
            for i, k in enumerate(order):
                new.S[k] = True
                if i >= n - new.lcap:
                    new.lir.add(k)
                else:
                    new.Q[k] = True
            new._prune()
        new.store = old.store
        self.real = new
        self.cur = best

    def access(self, key):
        freqs = self.freqs
        for j, f in enumerate(freqs):
            f[key] = f.get(key, 0) + 1
            self.ops[j] += 1
            if self.ops[j] >= self.resets[j]:
                self.ops[j] = 0
                freqs[j] = {k: v >> 1 for k, v in f.items() if v > 1}
        d = self.decay
        sc = self.scores
        for i, s in enumerate(self.shadows):
            sc[i] = sc[i] * d + s.access(key)
        self.n += 1
        if self.n >= self.every:
            self.n = 0
            best = max(range(len(sc)), key=lambda i: sc[i])
            if best != self.cur:
                mg = self.margin if self.conf[best][0] == self.conf[self.cur][0] else self.fmargin
                if sc[best] > sc[self.cur] * (1 + mg) + 1:
                    self._switch(best)
        return self.real.access(key)
