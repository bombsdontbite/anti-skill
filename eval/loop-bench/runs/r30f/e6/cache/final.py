from collections import OrderedDict


class Cache:
    """LIRS with HIR share adapted by reuse distance of non-resident stack hits:
    distance < capacity (an LRU would have hit) grows HIR; otherwise shrinks it."""

    STEP_DIV = 0

    def __init__(self, capacity):
        self.capacity = capacity
        self.hir_min = max(1, capacity // 100)
        self.hir_max = max(2, capacity // 2)
        self.hir_t = self.hir_min
        self.step = max(1, capacity // self.STEP_DIV) if self.STEP_DIV else 1
        self.S = OrderedDict()   # stack: key -> last access time
        self.Q = OrderedDict()   # resident HIR queue
        self.lir = set()
        self.store = {}
        self.t = 0
        self.stack_lim = capacity * 4

    def _prune(self):
        while self.S:
            k = next(iter(self.S))
            if k in self.lir:
                break
            del self.S[k]

    def _demote(self):
        k = next(iter(self.S))
        del self.S[k]; self.lir.discard(k)
        self.Q[k] = True
        self._prune()

    def _lir_cap(self):
        return self.capacity - self.hir_t

    def access(self, key):
        self.t += 1
        t = self.t
        if key in self.store:
            if key in self.lir:
                del self.S[key]; self.S[key] = t
                self._prune()
            else:
                if key in self.S:
                    del self.S[key]; self.S[key] = t
                    self.lir.add(key); del self.Q[key]
                    while len(self.lir) > self._lir_cap():
                        self._demote()
                else:
                    self.S[key] = t
                    self.Q.move_to_end(key)
            return True
        if len(self.store) >= self.capacity:
            if self.Q:
                k, _ = self.Q.popitem(last=False); del self.store[k]
            else:
                k = next(iter(self.S)); del self.S[k]; self.lir.discard(k); del self.store[k]; self._prune()
        self.store[key] = True
        if key in self.S:
            if t - self.S[key] < self.capacity:
                self.hir_t = min(self.hir_max, self.hir_t + self.step)
            else:
                self.hir_t = max(self.hir_min, self.hir_t - self.step)
            del self.S[key]; self.S[key] = t
            self.lir.add(key)
            while len(self.lir) > self._lir_cap():
                self._demote()
        elif len(self.lir) < self._lir_cap():
            self.S[key] = t; self.lir.add(key)
        else:
            self.S[key] = t
            self.Q[key] = True
        if len(self.S) > self.stack_lim:
            for k in list(self.S)[: len(self.S) - self.capacity * 3]:
                if k not in self.lir:
                    del self.S[k]
        return False
