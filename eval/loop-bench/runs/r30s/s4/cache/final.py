from collections import OrderedDict

HIR = 0.01
LEVELS = [0.01, 0.02, 0.04, 0.08, 0.16, 0.3]
EPS = 0.005
WF = 8
K = 1.0
ALPHA = 0.002


class Cache:
    """LIRS: stack S (recency order with status) and queue Q of resident HIRs."""

    def __init__(self, capacity):
        self.cap = capacity
        self.hcap = max(1, int(capacity * HIR))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict()  # key -> True if LIR else False (HIR resident) / None (non-resident)
        self.Q = OrderedDict()
        self.nlir = 0
        self.store = set()
        self.maxS = capacity * 3
        self.w = self.wh = 0
        self.W = capacity * WF
        self.prev = 0.0
        self.d = 1
        self.idx = 0
        self.hmin = max(1, int(capacity * HIR))
        self.target = self.hmin

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if S[k] is True:
                break
            del S[k]

    def _demote_bottom(self):
        S = self.S
        k = next(iter(S))
        del S[k]
        self.nlir -= 1
        self.Q[k] = True
        self._prune()

    def _trim(self):
        S = self.S
        while len(S) > self.maxS:
            # drop oldest non-LIR entry (non-resident preferred)
            for k, v in S.items():
                if v is not True:
                    del S[k]
                    break
            else:
                break

    def access(self, key):
        r = self._access(key)
        self.w += 1
        if r:
            self.wh += 1
        if self.w >= self.W:
            rate = self.wh / self.w
            if rate < self.prev - EPS:
                self.d = -self.d
            i = self.idx + self.d
            if i < 0 or i >= len(LEVELS):
                self.d = -self.d
                i = self.idx + self.d
            self.idx = i
            self.prev = rate
            self.w = self.wh = 0
            self.target = max(self.hmin, int(self.cap * LEVELS[i]))
        return r

    def _access(self, key):
        S, Q = self.S, self.Q
        st = S.get(key, 0)
        if st is True:
            was_bottom = next(iter(S)) == key
            S.move_to_end(key)
            if was_bottom:
                self._prune()
            return True
        if key in self.store:
            if st is False:
                # resident HIR in S: promote
                del S[key]
                S[key] = True
                del Q[key]
                self.nlir += 1
                self._demote_bottom()
            else:
                S[key] = False
                Q.move_to_end(key)
            return True
        # miss
        h = self.target
        if h != self.hcap:
            self.hcap = h
            self.lcap = self.cap - h
            while self.nlir > self.lcap:
                self._demote_bottom()
        while len(self.store) >= self.cap and Q:
            v, _ = Q.popitem(last=False)
            self.store.discard(v)
            if v in S:
                S[v] = None
        st = S.pop(key, 0)
        if self.nlir < self.lcap:
            S[key] = True
            self.nlir += 1
            self.store.add(key)
            return False
        while len(Q) >= self.hcap:
            v, _ = Q.popitem(last=False)
            self.store.discard(v)
            if v in S:
                S[v] = None
        self.store.add(key)
        if st is None:
            S[key] = True
            self.nlir += 1
            self._demote_bottom()
        else:
            S[key] = False
            Q[key] = True
        self._trim()
        return False
