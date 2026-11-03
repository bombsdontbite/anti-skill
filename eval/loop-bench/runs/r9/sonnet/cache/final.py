from collections import OrderedDict

HDIV = 100
NRES = 4


class Cache:
    def __init__(self, capacity):
        self.cap = capacity
        self.lhirs = max(1, capacity // HDIV)
        self.llirs = capacity - self.lhirs
        self.S = OrderedDict()  # key -> 'L' | 'H' | 'N'
        self.Q = OrderedDict()
        self.nonres = OrderedDict()
        self.nlir = 0
        self.store = set()

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            st = S[k]
            if st == 'L':
                return
            del S[k]
            if st == 'N':
                self.nonres.pop(k, None)

    def _demote_bottom(self):
        S = self.S
        if not self.nlir:
            return
        self._prune()
        k = next(iter(S))
        del S[k]
        self.nlir -= 1
        self.Q[k] = True
        self._prune()

    def _evict(self):
        if not self.Q:
            self._demote_bottom()
        k, _ = self.Q.popitem(last=False)
        self.store.discard(k)
        if k in self.S:
            self.S[k] = 'N'
            self.nonres[k] = True
            if len(self.nonres) > NRES * self.cap:
                o, _ = self.nonres.popitem(last=False)
                if self.S.get(o) == 'N':
                    del self.S[o]

    def access(self, key):
        S, Q = self.S, self.Q
        st = S.get(key)
        if st == 'L':
            S.move_to_end(key)
            self._prune()
            return True
        if key in Q:
            if st == 'H':
                del S[key]
                del Q[key]
                S[key] = 'L'
                self.nlir += 1
                self._demote_bottom()
            else:
                S[key] = 'H'
                Q.move_to_end(key)
            return True
        if len(self.store) >= self.cap:
            self._evict()
            st = S.get(key)
        self.store.add(key)
        if st == 'N':
            self.nonres.pop(key, None)
            del S[key]
            S[key] = 'L'
            self.nlir += 1
            self._demote_bottom()
        elif self.nlir < self.llirs:
            S[key] = 'L'
            self.nlir += 1
        else:
            S[key] = 'H'
            Q[key] = True
        return False
