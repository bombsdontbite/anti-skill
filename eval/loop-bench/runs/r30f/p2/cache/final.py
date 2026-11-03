from collections import OrderedDict


class Cache:
    """LIRS (low inter-reference recency set) whose HIR queue size follows a shadow LRU.

    S: recency stack over LIR keys, resident HIR keys and non-resident HIR keys.
    Q: resident HIR keys, FIFO eviction order.  H: non-LIR keys that sit in S, in
    insertion order, so the stack can be bounded in constant time.  L: shadow LRU
    of the same capacity.  Every window, if the shadow LRU hit more than we did the
    queue grows (toward LRU behaviour), otherwise it shrinks back.
    """

    def __init__(self, capacity, hir_frac=0.02, stack_mult=3, window=500,
                 max_frac=0.5, grow=2.0, shrink=0.5, margin=0.02):
        self.capacity = capacity
        self.min_q = max(1, int(capacity * hir_frac))
        self.max_q = max(1, int(capacity * max_frac))
        self.q_cap = self.min_q
        self.window = window
        self.grow = grow
        self.shrink = shrink
        self.margin = int(window * margin)
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.H = OrderedDict()
        self.L = OrderedDict()
        self.lir = set()
        self.store = {}
        self.max_s = capacity * stack_mult
        self.n = 0
        self.hits = 0
        self.lru_hits = 0

    def _shadow(self, key):
        L = self.L
        if key in L:
            L.move_to_end(key)
            self.lru_hits += 1
        else:
            if len(L) >= self.capacity:
                L.popitem(last=False)
            L[key] = True
        self.n += 1
        if self.n >= self.window:
            if self.lru_hits > self.hits + self.margin:
                self.q_cap = min(self.max_q, int(self.q_cap * self.grow) + 1)
            elif self.hits > self.lru_hits + self.margin:
                self.q_cap = max(self.min_q, int(self.q_cap * self.shrink))
            self.n = self.hits = self.lru_hits = 0

    def _prune(self):
        S, lir, H = self.S, self.lir, self.H
        while S:
            k = next(iter(S))
            if k in lir:
                return
            del S[k]
            del H[k]

    def _demote_bottom_lir(self):
        k = next(iter(self.S))
        del self.S[k]
        self.lir.discard(k)
        self.Q[k] = True
        self._prune()

    def _push(self, key):
        S, H = self.S, self.H
        S[key] = True
        H[key] = True
        if len(S) > self.max_s:
            k = next(iter(H))
            del H[k]
            del S[k]

    def _make_lir(self, key):
        S = self.S
        del S[key]
        del self.H[key]
        S[key] = True
        self.lir.add(key)
        while len(self.lir) > self.capacity - self.q_cap:
            self._demote_bottom_lir()

    def access(self, key):
        self._shadow(key)
        S, Q, store = self.S, self.Q, self.store
        if key in self.lir:
            self.hits += 1
            S.move_to_end(key)
            if next(iter(S)) not in self.lir:
                self._prune()
            return True
        if key in store:
            self.hits += 1
            if key in S:
                del Q[key]
                self._make_lir(key)
            else:
                self._push(key)
                Q.move_to_end(key)
            return True
        if len(self.lir) < self.capacity - self.q_cap and not Q:
            S[key] = True
            self.lir.add(key)
            store[key] = True
            return False
        if len(store) >= self.capacity:
            if not Q:
                self._demote_bottom_lir()
            k = next(iter(Q))
            del Q[k]
            del store[k]
        store[key] = True
        if key in S:
            self._make_lir(key)
        else:
            self._push(key)
            Q[key] = True
        return False
