"""Follow-the-leader over two shadow policies, LIRS and ARC.

Both run on every request; the real store tracks whichever has more recent
(exponentially decayed) hits, switching only on a clear margin. After a switch,
keys the new leader does not hold are evicted first.
"""
from collections import OrderedDict

LIR, HIR, NR = 0, 1, 2
HFRAC = 0.01
SMULT = 3
DECAY_MULT = 4.0
MARGIN = 0.05


class Lirs:
    def __init__(self, capacity, hfrac=HFRAC):
        self.cap = capacity
        self.hcap = max(1, int(capacity * hfrac))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.st = {}
        self.store = set()
        self.nlir = 0
        self.smax = SMULT * capacity
        self.ev = []

    def _prune(self):
        S = self.S; st = self.st
        while S:
            k = next(iter(S))
            s = st[k]
            if s == LIR:
                break
            del S[k]
            if s == NR:
                del st[k]

    def _demote(self):
        k, _ = self.S.popitem(last=False)
        self.st[k] = HIR
        self.Q[k] = True
        self.nlir -= 1
        self._prune()

    def _bound(self):
        S = self.S; st = self.st
        if len(S) > self.smax + self.cap:
            for k in list(S):
                if len(S) <= self.smax:
                    break
                if st[k] == NR:
                    del S[k]; del st[k]

    def access(self, x):
        st = self.st; S = self.S; Q = self.Q
        s = st.get(x)
        if s == LIR:
            S.move_to_end(x)
            self._prune()
            return True
        if s == HIR:
            if x in S:
                S.move_to_end(x)
                del Q[x]
                st[x] = LIR
                self.nlir += 1
                self._demote()
            else:
                S[x] = True
                Q.move_to_end(x)
            return True
        if len(self.store) >= self.cap:
            k, _ = Q.popitem(last=False)
            self.store.discard(k)
            self.ev.append(k)
            if k in S:
                st[k] = NR
            else:
                del st[k]
        self.store.add(x)
        if self.nlir < self.lcap:
            S[x] = True
            S.move_to_end(x)
            st[x] = LIR
            self.nlir += 1
            return False
        if s == NR:
            S.move_to_end(x)
            st[x] = LIR
            self.nlir += 1
            self._demote()
        else:
            S[x] = True
            st[x] = HIR
            Q[x] = True
        self._bound()
        return False


class Arc:
    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = set()
        self.ev = []

    def _replace(self, inb2):
        if self.t1 and (len(self.t1) > self.p or (inb2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        self.store.discard(k)
        self.ev.append(k)

    def access(self, x):
        c = self.c
        if x in self.t1:
            del self.t1[x]; self.t2[x] = True; return True
        if x in self.t2:
            self.t2.move_to_end(x); return True
        if x in self.b1:
            self.p = min(c, self.p + max(len(self.b2) // max(1, len(self.b1)), 1))
            self._replace(False); del self.b1[x]; self.t2[x] = True; self.store.add(x); return False
        if x in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // max(1, len(self.b2)), 1))
            self._replace(True); del self.b2[x]; self.t2[x] = True; self.store.add(x); return False
        l1 = len(self.t1) + len(self.b1)
        if l1 == c:
            if len(self.t1) < c:
                self.b1.popitem(last=False); self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False); self.store.discard(k); self.ev.append(k)
        else:
            tot = l1 + len(self.t2) + len(self.b2)
            if tot >= c:
                if tot == 2 * c:
                    self.b2.popitem(last=False)
                self._replace(False)
        self.t1[x] = True; self.store.add(x); return False


class Cache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.experts = [Lirs(capacity), Arc(capacity)]
        self.scores = [0.0] * len(self.experts)
        self.decay = 1.0 - 1.0 / (DECAY_MULT * capacity)
        self.lead = 0
        self.store = set()
        self.extra = OrderedDict()  # keys in store but not in leader's store

    def access(self, key):
        store = self.store
        hit = key in store
        sc = self.scores; d = self.decay
        ex = self.experts
        for i in range(len(ex)):
            e = ex[i]
            e.ev = []
            sc[i] = sc[i] * d + (1.0 if e.access(key) else 0.0)
        best = self.lead
        thr = sc[best] * (1.0 + MARGIN) + 1.0
        for i in range(len(ex)):
            if sc[i] > thr:
                best = i
                thr = sc[i]
        extra = self.extra
        if best != self.lead:
            self.lead = best
            t = ex[best].store
            extra.clear()
            for k in store:
                if k not in t:
                    extra[k] = True
        else:
            t = ex[best].store
            for k in ex[best].ev:
                if k in store:
                    extra[k] = True
        if key in extra and key in t:
            del extra[key]
        if not hit:
            store.add(key)
            if key not in t:
                extra[key] = True
            if len(store) > self.capacity:
                if extra:
                    k, _ = extra.popitem(last=False)
                else:
                    k = next(k for k in store if k != key)
                store.discard(k)
        return hit
