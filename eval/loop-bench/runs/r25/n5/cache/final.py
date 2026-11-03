from collections import OrderedDict


class LIRS:

    def __init__(self, capacity, hir_frac=0.01, nr_mult=2):
        self.capacity = capacity
        self.lhirs = max(1, int(capacity * hir_frac))
        self.llirs = capacity - self.lhirs
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.NR = OrderedDict()
        self.lir = set()
        self.store = {}
        self.ev = []
        self.nrmax = int(capacity * nr_mult)

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if k in self.lir:
                return
            del S[k]
            self.NR.pop(k, None)

    def _demote_bottom(self):
        k, _ = self.S.popitem(last=False)
        self.lir.discard(k)
        self.Q[k] = True
        self._prune()

    def access(self, key):
        S = self.S
        if key in self.lir:
            first = next(iter(S)) == key
            S.move_to_end(key)
            if first:
                self._prune()
            return True
        if key in self.Q:
            if key in S:
                del self.Q[key]
                self.lir.add(key)
                S.move_to_end(key)
                self._demote_bottom()
            else:
                S[key] = True
                self.Q.move_to_end(key)
            return True
        if len(self.store) >= self.capacity:
            v, _ = self.Q.popitem(last=False)
            del self.store[v]
            self.ev.append(v)
            if v in S:
                self.NR[v] = True
                if len(self.NR) > self.nrmax:
                    o, _ = self.NR.popitem(last=False)
                    del S[o]
        self.store[key] = True
        if key in S:
            del self.NR[key]
            self.lir.add(key)
            S.move_to_end(key)
            self._demote_bottom()
        elif len(self.lir) < self.llirs:
            self.lir.add(key)
            S[key] = True
        else:
            S[key] = True
            self.Q[key] = True
        return False



class ARC:

    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = {}
        self.ev = []

    def _replace(self, in_b2):
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        del self.store[k]
        self.ev.append(k)

    def access(self, key):
        c = self.c
        if key in self.t1:
            del self.t1[key]; self.t2[key] = True; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p = min(c, self.p + max(1, len(self.b2) // max(1, len(self.b1))))
            self._replace(False); del self.b1[key]; self.t2[key] = True; self.store[key] = True
            return False
        if key in self.b2:
            self.p = max(0, self.p - max(1, len(self.b1) // max(1, len(self.b2))))
            self._replace(True); del self.b2[key]; self.t2[key] = True; self.store[key] = True
            return False
        l1 = len(self.t1) + len(self.b1)
        if l1 == c:
            if len(self.t1) < c:
                self.b1.popitem(last=False); self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False); del self.store[k]; self.ev.append(k)
        else:
            tot = l1 + len(self.t2) + len(self.b2)
            if tot >= c:
                if tot == 2 * c and self.b2:
                    self.b2.popitem(last=False)
                self._replace(False)
        self.t1[key] = True; self.store[key] = True
        return False


class Cache:
    """Simulates LIRS and ARC; the real store follows whichever has more recent hits."""

    def __init__(self, capacity, horizon=4, margin=0.02):
        self.capacity = capacity
        # LIRS needs at least one LIR slot
        self.pol = [LIRS(capacity), ARC(capacity)] if capacity > 1 else [ARC(capacity)]
        self.sc = [0.0] * len(self.pol)
        self.a = 1.0 / (capacity * horizon)
        self.margin = margin
        self.cur = 0
        self.store = set()
        self.extra = OrderedDict()

    def access(self, key):
        hit = key in self.store
        a = self.a
        sc = self.sc
        for i, p in enumerate(self.pol):
            p.ev = []
            h = p.access(key)
            sc[i] += a * (h - sc[i])
        best = 0
        for i in range(1, len(sc)):
            if sc[i] > sc[best]:
                best = i
        if best != self.cur and sc[best] > sc[self.cur] + self.margin:
            self.cur = best
            t = self.pol[best].store
            self.extra = OrderedDict((k, True) for k in self.store if k not in t)
        else:
            for k in self.pol[self.cur].ev:
                self.store.discard(k)
        t = self.pol[self.cur].store
        if key in t:
            self.extra.pop(key, None)
            self.store.add(key)
            while len(self.store) > self.capacity:
                k, _ = self.extra.popitem(last=False)
                self.store.discard(k)
        return hit
