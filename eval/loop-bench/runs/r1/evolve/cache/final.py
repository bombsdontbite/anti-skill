from collections import OrderedDict
from itertools import islice


class Cache:
    """LIRS; HIR victim is the least frequent of the oldest few in Q."""

    def __init__(self, capacity):
        self.cap = capacity
        self.hcap = max(1, capacity // 100)
        self.lcap = capacity - self.hcap
        self.S = OrderedDict()  # key -> True; most recent at end
        self.Q = OrderedDict()  # resident HIR
        self.lir = set()
        self.store = {}
        self.maxS = 3 * capacity
        self.freq = {}
        self.ops = 0
        self.sample = max(2, capacity // 50)

    def _inc(self, key):
        f = self.freq
        f[key] = min(f.get(key, 0) + 1, 15)
        self.ops += 1
        if self.ops >= 10 * self.cap:
            self.ops = 0
            self.freq = {k: v >> 1 for k, v in f.items() if v > 1}

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if k in self.lir:
                break
            del S[k]

    def _demote_bottom_lir(self):
        S = self.S
        k, _ = S.popitem(last=False)
        self.lir.discard(k)
        self.Q[k] = True
        self._prune()

    def access(self, key):
        S, Q, lir = self.S, self.Q, self.lir
        self._inc(key)
        if key in lir:
            first = next(iter(S))
            S.move_to_end(key)
            if first == key:
                self._prune()
            return True
        if key in self.store:
            # resident HIR
            if key in S:
                S.move_to_end(key)
                del Q[key]
                lir.add(key)
                self._demote_bottom_lir()
            else:
                S[key] = True
                Q.move_to_end(key)
            return True
        # miss
        if len(lir) < self.lcap:
            S[key] = True
            S.move_to_end(key)
            lir.add(key)
            self.store[key] = True
            return False
        if len(self.store) >= self.cap:
            fg = self.freq.get
            v = min(islice(Q, self.sample), key=lambda k: fg(k, 0))
            del Q[v]
            del self.store[v]
        self.store[key] = True
        if key in S:
            S.move_to_end(key)
            lir.add(key)
            self._demote_bottom_lir()
        else:
            S[key] = True
            Q[key] = True
        if len(S) > self.maxS:
            # drop oldest non-resident HIR entries
            for k in list(S.keys()):
                if len(S) <= self.maxS:
                    break
                if k not in lir and k not in self.store:
                    del S[k]
        return False
