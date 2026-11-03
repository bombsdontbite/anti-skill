from collections import OrderedDict


class Cache:
    """LIRS whose resident-HIR share grows while a shadow LRU is out-hitting it."""

    def __init__(self, capacity):
        self.cap = capacity
        self.hmin = max(1, int(capacity * 0.01))
        self.hmax = max(1, int(capacity * 0.5))
        self.hcap = self.hmin
        self.S = OrderedDict()   # recency stack: LIR, resident HIR, non-resident HIR
        self.Q = OrderedDict()   # resident HIR, FIFO
        self.NR = OrderedDict()  # non-resident HIR still in S, oldest first
        self.lir = set()
        self.store = set()
        self.maxNR = capacity * 3
        self.shadow = OrderedDict()
        self.period = capacity * 4
        self.step = max(1, int(capacity * 0.03))
        self.n = 0
        self.hits = 0
        self.lhits = 0

    def _prune(self):
        S, lir, NR = self.S, self.lir, self.NR
        while S:
            k = next(iter(S))
            if k in lir:
                break
            del S[k]
            NR.pop(k, None)

    def _demote(self):
        S = self.S
        b = next(iter(S))
        del S[b]
        self.lir.discard(b)
        self.Q[b] = True
        self._prune()

    def _adapt(self):
        if self.lhits > self.hits:
            self.hcap = min(self.hmax, self.hcap + self.step)
        else:
            self.hcap = max(self.hmin, self.hcap - self.step)
        while len(self.lir) > self.cap - self.hcap:
            self._demote()
        self.hits = self.lhits = 0

    def access(self, x):
        sh = self.shadow
        if x in sh:
            sh.move_to_end(x)
            self.lhits += 1
        else:
            sh[x] = True
            if len(sh) > self.cap:
                sh.popitem(last=False)
        self.n += 1
        if self.n >= self.period:
            self.n = 0
            self._adapt()

        S, Q, lir = self.S, self.Q, self.lir
        if x in lir:
            first = next(iter(S)) == x
            S.move_to_end(x)
            if first:
                self._prune()
            self.hits += 1
            return True
        hit = x in self.store
        if hit:
            self.hits += 1
        else:
            if len(lir) < self.cap - self.hcap and len(self.store) < self.cap:
                lir.add(x)
                self.store.add(x)
                S[x] = True
                S.move_to_end(x)
                self.NR.pop(x, None)
                return False
            if len(self.store) >= self.cap:
                k, _ = Q.popitem(last=False)
                self.store.discard(k)
                if k in S:
                    self.NR[k] = True
                    if len(self.NR) > self.maxNR:
                        o, _ = self.NR.popitem(last=False)
                        del S[o]
            self.store.add(x)
        if x in S:
            S.move_to_end(x)
            Q.pop(x, None)
            self.NR.pop(x, None)
            lir.add(x)
            self._demote()
            while len(lir) > self.cap - self.hcap:
                self._demote()
        else:
            S[x] = True
            Q[x] = True
            Q.move_to_end(x)
        return hit
