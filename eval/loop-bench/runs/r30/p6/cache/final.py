from collections import OrderedDict

L, H, N = 0, 1, 2


class Cache:
    """LIRS."""

    def __init__(self, capacity):
        self.c = capacity
        self.hir_max = max(1, int(capacity * 0.05))
        self.lir_max = capacity - self.hir_max
        self.lir = 0
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.store = set()
        self.nres_cap = 2 * capacity
        self.nres = 0

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            st = S[k]
            if st == L:
                break
            del S[k]
            if st == N:
                self.nres -= 1

    def _demote_bottom(self):
        S = self.S
        k = next(iter(S))
        del S[k]
        self.lir -= 1
        self.Q[k] = True
        self._prune()

    def access(self, key):
        S, Q = self.S, self.Q
        st = S.get(key)
        if st == L:
            S.move_to_end(key)
            self._prune()
            return True
        if st == H:
            S.move_to_end(key)
            del Q[key]
            S[key] = L
            self.lir += 1
            self._demote_bottom()
            return True
        if key in Q:
            S[key] = H
            Q.move_to_end(key)
            return True
        # miss
        if len(self.store) >= self.c:
            v, _ = Q.popitem(last=False)
            self.store.discard(v)
            if v in S:
                S[v] = N
                self.nres += 1
                if self.nres > self.nres_cap:
                    for k in S:
                        if S[k] == N:
                            del S[k]
                            self.nres -= 1
                            break
        st = S.get(key)
        self.store.add(key)
        if st == N:
            del S[key]
            self.nres -= 1
            S[key] = L
            self.lir += 1
            self._demote_bottom()
        elif self.lir < self.lir_max:
            S[key] = L
            self.lir += 1
        else:
            S[key] = H
            Q[key] = True
        return False
