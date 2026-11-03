from collections import OrderedDict


class Cache:
    """LIRS (low inter-reference recency set) with an adaptive HIR share.

    Keys with a short reuse distance are LIR and stay resident; everything else is HIR and
    passes through a small resident queue Q, so scans and loops larger than the cache cannot
    flush the hot set. Stack S also remembers recently evicted keys, so a looping key seen
    again is promoted to LIR instead of being evicted again (LRU gets zero hits on such loops).
    The HIR share grows by 2 on each resident-HIR hit (a recency-friendly signal) and shrinks
    by 1 on each non-resident hit (a loop signal), so recency-driven traces get LRU-like hits.
    """

    def __init__(self, capacity):
        self.c = capacity
        self.hmin = max(1, capacity // 100)
        self.hc = self.hmin
        self.lc = capacity - self.hc
        self.S = OrderedDict()   # key -> 'L' (LIR), 'H' (resident HIR), 'N' (non-resident HIR)
        self.Q = OrderedDict()   # resident HIR keys in FIFO order
        self.store = {}
        self.nlir = 0

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if S[k] == 'L':
                break
            S.pop(k)
        while len(S) > 3 * self.c:
            k = next(iter(S))
            if S[k] == 'L':
                break
            S.pop(k)

    def _evict_hir(self):
        k, _ = self.Q.popitem(last=False)
        del self.store[k]
        if k in self.S:
            self.S[k] = 'N'

    def _demote(self):
        S, Q = self.S, self.Q
        while self.nlir > self.lc:
            k = next(iter(S)); S.pop(k); self.nlir -= 1
            Q[k] = True
            self._prune()

    def access(self, key):
        S, Q = self.S, self.Q
        if key in self.store:
            st = S.get(key)
            if st == 'L':
                S.move_to_end(key); self._prune()
            elif st == 'H':
                if self.hc < self.c // 2:
                    self.hc += 2; self.lc = self.c - self.hc
                del S[key]; S[key] = 'L'; self.nlir += 1
                del Q[key]
                self._demote()
            else:
                Q.move_to_end(key); S[key] = 'H'
            return True
        if len(self.store) >= self.c:
            if Q:
                self._evict_hir()
            else:
                k = next(iter(S)); S.pop(k); self.nlir -= 1; del self.store[k]; self._prune()
        if self.nlir < self.lc:
            S[key] = 'L'; self.nlir += 1; self.store[key] = True
            return False
        st = S.pop(key, None)
        if st == 'N':
            if self.hc > self.hmin + 1:
                self.hc -= 1; self.lc = self.c - self.hc
            S[key] = 'L'; self.nlir += 1; self.store[key] = True
            self._demote()
        else:
            S[key] = 'H'; Q[key] = True; self.store[key] = True
        while len(Q) > self.hc:
            self._evict_hir()
        return False
