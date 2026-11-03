from collections import OrderedDict

HIR = 0.05


class Cache:
    """LIRS: low inter-reference recency set. Stack S (LIR + resident/non-resident HIR), queue Q (resident HIR)."""

    def __init__(self, capacity):
        self.c = capacity
        self.hcap = max(1, int(capacity * HIR))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict()   # key -> status: 'L' lir, 'H' resident hir, 'N' nonresident hir
        self.Q = OrderedDict()   # resident HIR keys
        self.store = {}
        self.nlir = 0
        self.max_s = capacity * 3

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            st = S[k]
            if st == 'L':
                return
            del S[k]
            # if key leaves S and is resident HIR, it remains in Q (fine)

    def _demote_lir(self):
        # bottom of S is LIR; move to HIR resident (end of Q) and prune
        k = next(iter(self.S))
        del self.S[k]
        self.nlir -= 1
        self.Q[k] = True
        self._prune()

    def _evict_hir(self):
        k, _ = self.Q.popitem(last=False)
        del self.store[k]
        if k in self.S:
            self.S[k] = 'N'

    def access(self, key):
        S, Q = self.S, self.Q
        if key in self.store:
            st = S.get(key)
            if st == 'L':
                S.move_to_end(key)
                self._prune()
            elif st == 'H':
                # in S and resident HIR: promote to LIR
                del S[key]; S[key] = 'L'; self.nlir += 1
                del Q[key]
                if self.nlir > self.lcap:
                    self._demote_lir()
            else:
                # resident HIR not in S: move to top of S, stays HIR; move to end of Q
                S[key] = 'H'
                Q.move_to_end(key)
            return True
        # miss
        if len(self.store) >= self.c:
            if Q:
                self._evict_hir()
            else:
                self._demote_lir()
                self._evict_hir()
        self.store[key] = True
        if self.nlir < self.lcap and key not in S:
            S[key] = 'L'; self.nlir += 1
        elif S.get(key) == 'N':
            del S[key]; S[key] = 'L'; self.nlir += 1
            if self.nlir > self.lcap:
                self._demote_lir()
        else:
            if key in S:
                del S[key]
            S[key] = 'H'
            Q[key] = True
        if len(S) > self.max_s:
            for k in [k for k, st in S.items() if st == 'N']:
                del S[k]
        return False
