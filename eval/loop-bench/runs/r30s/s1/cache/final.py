from collections import OrderedDict
HIR = 0.05
NR = 3.0
DEC = 0.3
GROW = 3.0
MAXH = 0.2
MINH = 0.02

class Cache:
    def __init__(self, capacity):
        self.cap = capacity
        self.h = max(1.0, capacity * HIR)
        self.lirs = capacity - int(self.h)
        self.filled = False
        self.S = OrderedDict()   # key -> 0 LIR, 1 resident HIR, 2 nonresident
        self.Q = OrderedDict()
        self.nlir = 0
        self.nr = OrderedDict()
        self.nrmax = int(capacity * NR)
        self.store = set()

    def _grow(self):
        self.h = min(self.cap * MAXH, self.h + GROW)
        self.lirs = self.cap - int(self.h)

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if S[k] == 0: break
            del S[k]
            self.nr.pop(k, None)

    def _demote_bottom(self):
        S = self.S
        if self.nlir <= self.lirs:
            return
        k = next(iter(S))
        del S[k]
        self.nlir -= 1
        self.Q[k] = None
        self._prune()
        S_ = None

    def access(self, key):
        S = self.S; Q = self.Q
        st = S.get(key)
        if st == 0:
            S.move_to_end(key)
            self._prune()
            return True
        if st == 1:
            self._grow()
            del Q[key]
            S[key] = 0; S.move_to_end(key)
            self.nlir += 1
            self._demote_bottom()
            while self.nlir > self.lirs: self._demote_bottom()
            return True
        if key in Q:
            self._grow()
            Q.move_to_end(key); S[key] = 1
            return True
        # miss
        if not self.filled and self.nlir < self.lirs:
            S[key] = 0; self.nlir += 1; self.store.add(key)
            return False
        if len(self.store) >= self.cap:
            self.filled = True
            self.h = max(self.cap * MINH, self.h - DEC)
            self.lirs = self.cap - int(self.h)
            v, _ = Q.popitem(last=False)
            self.store.discard(v)
            if v in S:
                S[v] = 2; self.nr[v] = None
                if len(self.nr) > self.nrmax:
                    o, _ = self.nr.popitem(last=False); del S[o]
        self.store.add(key)
        st = S.get(key)
        if st == 2:
            del self.nr[key]
            S[key] = 0; S.move_to_end(key); self.nlir += 1
            while self.nlir > self.lirs: self._demote_bottom()
        else:
            S[key] = 1; Q[key] = None
        return False
