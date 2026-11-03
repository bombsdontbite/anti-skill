from collections import OrderedDict, deque


class _ARC:
    def __init__(self, capacity):
        self.capacity = capacity
        self.p = 0
        self.t1 = OrderedDict()
        self.t2 = OrderedDict()
        self.b1 = OrderedDict()
        self.b2 = OrderedDict()
        self.store = {}
        self.evicted = None

    def _replace(self, in_b2):
        t1, t2 = self.t1, self.t2
        if t1 and (len(t1) > self.p or (in_b2 and len(t1) == self.p)):
            k, _ = t1.popitem(last=False)
            self.b1[k] = True
        else:
            k, _ = t2.popitem(last=False)
            self.b2[k] = True
        del self.store[k]
        self.evicted = k

    def access(self, key):
        t1, t2, b1, b2 = self.t1, self.t2, self.b1, self.b2
        c = self.capacity
        self.evicted = None
        if key in t1:
            del t1[key]
            t2[key] = True
            return True
        if key in t2:
            t2.move_to_end(key)
            return True
        if key in b1:
            d = max(1, len(b2) // len(b1))
            self.p = min(c, self.p + d)
            self._replace(False)
            del b1[key]
            t2[key] = True
            self.store[key] = True
            return False
        if key in b2:
            d = max(1, len(b1) // len(b2))
            self.p = max(0, self.p - d)
            self._replace(True)
            del b2[key]
            t2[key] = True
            self.store[key] = True
            return False
        l1 = len(t1) + len(b1)
        if l1 == c:
            if len(t1) < c:
                b1.popitem(last=False)
                self._replace(False)
            else:
                k, _ = t1.popitem(last=False)
                del self.store[k]
                self.evicted = k
        elif l1 < c and l1 + len(t2) + len(b2) >= c:
            if l1 + len(t2) + len(b2) >= 2 * c:
                b2.popitem(last=False)
            self._replace(False)
        t1[key] = True
        self.store[key] = True
        return False


class _LIRS:
    def __init__(self, capacity):
        self.capacity = capacity
        self.hmax = max(1, capacity // 100)
        self.lmax = capacity - self.hmax
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.lir = set()
        self.store = {}
        self.nmax = capacity * 2
        self.evicted = None

    def _prune(self):
        S, lir = self.S, self.lir
        while S:
            k = next(iter(S))
            if k in lir:
                break
            del S[k]

    def _demote_bottom(self):
        S = self.S
        k = next(iter(S))
        del S[k]
        self.lir.discard(k)
        self.Q[k] = True
        self._prune()

    def _evict_hir(self):
        if self.Q:
            k, _ = self.Q.popitem(last=False)
        else:
            k = next(iter(self.S))
            del self.S[k]
            self.lir.discard(k)
            self._prune()
        del self.store[k]
        self.evicted = k

    def access(self, key):
        S, Q, lir, store = self.S, self.Q, self.lir, self.store
        self.evicted = None
        if key in lir:
            was_bottom = next(iter(S)) == key
            S.move_to_end(key)
            if was_bottom:
                self._prune()
            return True
        if key in store:
            if key in S:
                del S[key]
                S[key] = True
                lir.add(key)
                del Q[key]
                if len(lir) > self.lmax:
                    self._demote_bottom()
            else:
                S[key] = True
                Q.move_to_end(key)
            return True
        if len(store) >= self.capacity:
            self._evict_hir()
        store[key] = True
        if key in S:
            del S[key]
            S[key] = True
            lir.add(key)
            if len(lir) > self.lmax:
                self._demote_bottom()
        else:
            S[key] = True
            if len(lir) < self.lmax:
                lir.add(key)
            else:
                Q[key] = True
        if len(S) > self.lmax + self.nmax:
            target = self.lmax + self.nmax // 2
            for k in list(S):
                if len(S) <= target:
                    break
                if k in lir or k in store:
                    continue
                del S[k]
            self._prune()
        return False


class Cache:
    """Follows whichever shadow policy (LIRS or ARC) has the better recent hit rate."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.shadows = [_LIRS(capacity), _ARC(capacity)]
        self.scores = [0.0, 0.0]
        self.decay = 1.0 - 1.0 / max(200, capacity * 4)
        self.best = 0
        self.margin = 0.03
        self.store = OrderedDict()
        self.cands = deque()

    def access(self, key):
        store = self.store
        shadows, scores = self.shadows, self.scores
        dec = self.decay
        best = self.best
        for i in range(2):
            h = shadows[i].access(key)
            scores[i] = scores[i] * dec + (1.0 if h else 0.0)
        ev = shadows[best].evicted
        if ev is not None and ev in store:
            self.cands.append(ev)
        # maybe switch
        other = 1 - best
        if scores[other] > scores[best] + self.margin * (1.0 / (1.0 - dec)):
            self.best = best = other
            bs = shadows[best].store
            self.cands = deque(k for k in store if k not in bs)
        if key in store:
            store.move_to_end(key)
            return True
        if key not in shadows[best].store:
            return False
        if len(store) >= self.capacity:
            bs = shadows[best].store
            cands = self.cands
            victim = None
            while cands:
                v = cands.popleft()
                if v in store and v not in bs:
                    victim = v
                    break
            if victim is None:
                victim = next(iter(store))
            del store[victim]
        store[key] = True
        return False
