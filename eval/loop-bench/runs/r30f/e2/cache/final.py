from collections import OrderedDict


class Cache:
    """LIRS: low inter-reference recency set. Stack S (LIR + resident/non-resident HIR), queue Q (resident HIR)."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.hirs_cap = 1
        self.lirs_cap = max(1, capacity - self.hirs_cap)
        self.S = OrderedDict()   # key -> True ; stack, bottom first
        self.Q = OrderedDict()   # resident HIR
        self.lir = set()
        self.store = {}
        self.nonres_cap = capacity * 2

    def _prune(self):
        S = self.S
        lir = self.lir
        while S:
            k = next(iter(S))
            if k in lir:
                return
            del S[k]
            # non-resident HIR dropped from stack silently

    def _limit_stack(self):
        # bound stack size (non-resident entries) to keep memory & time sane
        S = self.S
        maxlen = self.capacity + self.nonres_cap
        if len(S) > maxlen:
            for k in list(S)[: len(S) - maxlen]:
                if k not in self.lir and k not in self.store:
                    del S[k]
            self._prune()

    def access(self, key):
        S = self.S
        Q = self.Q
        lir = self.lir
        store = self.store
        if key in lir:
            # LIR hit
            S.move_to_end(key)
            self._prune()
            return True
        if key in store:
            # resident HIR hit
            if key in S:
                del S[key]
                S[key] = True
                lir.add(key)
                del Q[key]
                # demote bottom LIR
                if len(lir) > self.lirs_cap:
                    b = next(iter(S))
                    del S[b]
                    lir.discard(b)
                    if b in store:
                        Q[b] = True
                    self._prune()
            else:
                S[key] = True
                Q.move_to_end(key)
            return True
        # miss
        if len(store) >= self.capacity:
            if Q:
                v, _ = Q.popitem(last=False)
                store.pop(v, None)
            else:
                b = next(iter(S))
                del S[b]
                lir.discard(b)
                del store[b]
                self._prune()
        store[key] = True
        if len(lir) < self.lirs_cap and key not in S:
            lir.add(key)
            S[key] = True
            return False
        if key in S:
            # non-resident HIR in stack: promote to LIR
            del S[key]
            S[key] = True
            lir.add(key)
            if len(lir) > self.lirs_cap:
                b = next(iter(S))
                del S[b]
                lir.discard(b)
                if b in store:
                    Q[b] = True
                self._prune()
        else:
            S[key] = True
            Q[key] = True
            self._limit_stack()
        return False
