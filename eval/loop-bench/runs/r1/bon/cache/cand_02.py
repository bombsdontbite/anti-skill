from collections import OrderedDict

LIR = 0
HIR = 1
NON = 2


class Cache:
    """LIRS: inter-reference recency decides who is protected; a small HIR queue absorbs scans."""

    def __init__(self, capacity):
        self.capacity = capacity
        hir = max(1, capacity // 100)
        if hir >= capacity:
            hir = capacity - 1
        self.lir_size = max(1, capacity - hir)
        self.nlir = 0
        self.S = OrderedDict()      # recency stack, last = top
        self.Q = OrderedDict()      # resident HIR keys, first = next victim
        self.state = {}
        self.non = OrderedDict()    # non-resident HIR keys still in S
        self.non_limit = 2 * capacity + 8
        self.store = {}

    def _prune(self):
        S = self.S
        st = self.state
        while S:
            k = next(iter(S))
            if st[k] == LIR:
                break
            S.popitem(last=False)
            if st[k] == NON:
                del st[k]
                self.non.pop(k, None)

    def _demote(self):
        k, _ = self.S.popitem(last=False)
        self.state[k] = HIR
        self.Q[k] = None
        self.nlir -= 1
        self._prune()

    def access(self, key):
        st = self.state
        S = self.S
        Q = self.Q
        s = st.get(key)
        if s == LIR:
            S.move_to_end(key)
            self._prune()
            return True
        if s == HIR:
            if key in S:
                S.move_to_end(key)
                del Q[key]
                st[key] = LIR
                self.nlir += 1
                if self.nlir > self.lir_size:
                    self._demote()
            else:
                S[key] = None
                Q.move_to_end(key)
            return True
        if len(self.store) >= self.capacity:
            if not Q:
                self._demote()
            v, _ = Q.popitem(last=False)
            del self.store[v]
            if v in S:
                st[v] = NON
                self.non[v] = None
                if len(self.non) > self.non_limit:
                    k, _ = self.non.popitem(last=False)
                    del S[k]
                    del st[k]
            else:
                del st[v]
        if key in self.non:
            del self.non[key]
            S.move_to_end(key)
            st[key] = LIR
            self.nlir += 1
            if self.nlir > self.lir_size:
                self._demote()
        elif self.nlir < self.lir_size:
            st[key] = LIR
            S[key] = None
            self.nlir += 1
        else:
            st[key] = HIR
            S[key] = None
            Q[key] = None
        self.store[key] = True
        return False
