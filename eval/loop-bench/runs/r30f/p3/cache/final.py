from collections import OrderedDict


class Cache:
    """LIRS whose LIR/HIR split follows a shadow LRU: grow the HIR queue when
    LRU would have hit and we missed, shrink it when we hit and LRU would not."""

    HMIN_FRAC = 0.01
    HMAX_FRAC = 0.9
    NR_MULT = 2.0

    def __init__(self, capacity):
        self.capacity = capacity
        self.hmin = max(1, int(capacity * self.HMIN_FRAC))
        self.hmax = max(self.hmin, int(capacity * self.HMAX_FRAC))
        self.hsize = self.hmin
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.st = {}  # key -> 0 LIR, 1 resident HIR, 2 nonresident HIR
        self.NR = OrderedDict()
        self.nr_limit = int(capacity * self.NR_MULT)
        self.store = {}
        self.nlir = 0
        self.shadow = OrderedDict()

    def _prune(self):
        S = self.S
        st = self.st
        while S:
            k = next(iter(S))
            if st[k] == 0:
                break
            del S[k]
            if st[k] == 2:
                del st[k]
                del self.NR[k]

    def _demote_bottom(self):
        self._prune()
        k = next(iter(self.S))
        del self.S[k]
        self.st[k] = 1
        self.Q[k] = True
        self.nlir -= 1
        self._prune()

    def _evict_one(self):
        if not self.Q:
            self._demote_bottom()
        k, _ = self.Q.popitem(last=False)
        del self.store[k]
        if k in self.S:
            self.st[k] = 2
            self.NR[k] = True
            if len(self.NR) > self.nr_limit:
                old, _ = self.NR.popitem(last=False)
                del self.S[old]
                del self.st[old]
        else:
            del self.st[k]

    def _shadow(self, key):
        sh = self.shadow
        if key in sh:
            sh.move_to_end(key)
            return True
        if len(sh) >= self.capacity:
            sh.popitem(last=False)
        sh[key] = True
        return False

    def access(self, key):
        lru_hit = self._shadow(key)
        S = self.S
        st = self.st
        s = st.get(key)
        if s == 0:
            first = next(iter(S)) == key
            S.move_to_end(key)
            if first:
                self._prune()
            if not lru_hit and self.hsize > self.hmin:
                self.hsize -= 1
            return True
        if s == 1:
            if key in S:
                S.move_to_end(key)
                st[key] = 0
                self.nlir += 1
                del self.Q[key]
                while self.nlir > self.capacity - self.hsize:
                    self._demote_bottom()
            else:
                self.Q.move_to_end(key)
                S[key] = True
            if not lru_hit and self.hsize > self.hmin:
                self.hsize -= 1
            return True
        # miss
        if lru_hit and self.hsize < self.hmax:
            self.hsize += 1
        store = self.store
        if s == 2:
            del self.NR[key]
        lsize = self.capacity - self.hsize
        if len(store) < self.capacity:
            store[key] = True
            if self.nlir < lsize:
                st[key] = 0
                self.nlir += 1
                S[key] = True
            else:
                st[key] = 1
                S[key] = True
                self.Q[key] = True
            return False
        self._evict_one()
        store[key] = True
        if s == 2:
            S.move_to_end(key)
            st[key] = 0
            self.nlir += 1
        else:
            st[key] = 1
            S[key] = True
            self.Q[key] = True
        while self.nlir > lsize:
            self._demote_bottom()
        return False
