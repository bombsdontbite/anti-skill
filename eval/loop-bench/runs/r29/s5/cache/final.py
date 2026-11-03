from collections import OrderedDict


class ARC:
    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1, self.t2, self.b1, self.b2 = OrderedDict(), OrderedDict(), OrderedDict(), OrderedDict()
        self.store = {}
        self.ev = []

    def _replace(self, in_b2):
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False)
            self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False)
            self.b2[k] = True
        del self.store[k]
        self.ev.append(k)

    def access(self, key):
        c = self.c
        if key in self.t1:
            del self.t1[key]
            self.t2[key] = True
            return True
        if key in self.t2:
            self.t2.move_to_end(key)
            return True
        if key in self.b1:
            self.p = min(c, self.p + max(1, len(self.b2) // len(self.b1)))
            self._replace(False)
            del self.b1[key]
            self.t2[key] = True
            self.store[key] = True
            return False
        if key in self.b2:
            self.p = max(0, self.p - max(1, len(self.b1) // len(self.b2)))
            self._replace(True)
            del self.b2[key]
            self.t2[key] = True
            self.store[key] = True
            return False
        l1 = len(self.t1) + len(self.b1)
        if l1 == c:
            if len(self.t1) < c:
                self.b1.popitem(last=False)
                self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False)
                del self.store[k]
                self.ev.append(k)
        else:
            tot = l1 + len(self.t2) + len(self.b2)
            if tot >= c:
                if tot == 2 * c:
                    self.b2.popitem(last=False)
                self._replace(False)
        self.t1[key] = True
        self.store[key] = True
        return False


class LIRS:
    def __init__(self, capacity, hir=0.01, ghost=2.0):
        self.capacity = capacity
        self.lir_cap = max(1, capacity - max(1, int(capacity * hir)))
        self.store = {}
        self.ev = []
        self.lir = set()
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.nonres = OrderedDict()
        self.max_nonres = int(ghost * capacity)

    def _prune(self):
        S, lir = self.S, self.lir
        while S:
            k = next(iter(S))
            if k in lir:
                return
            del S[k]
            self.nonres.pop(k, None)

    def _demote(self):
        y, _ = self.S.popitem(last=False)
        self.lir.discard(y)
        self.Q[y] = True
        self._prune()

    def access(self, x):
        S = self.S
        if x in self.lir:
            bottom = next(iter(S)) == x
            S.move_to_end(x)
            if bottom:
                self._prune()
            return True
        if x in self.Q:
            if x in S:
                S.move_to_end(x)
                del self.Q[x]
                self.lir.add(x)
                self._demote()
            else:
                S[x] = True
                self.Q.move_to_end(x)
            return True
        self.store[x] = True
        if len(self.store) > self.capacity:
            z, _ = self.Q.popitem(last=False)
            del self.store[z]
            self.ev.append(z)
            if z in S:
                self.nonres[z] = True
                if len(self.nonres) > self.max_nonres:
                    k, _ = self.nonres.popitem(last=False)
                    del S[k]
        if len(self.lir) < self.lir_cap and not self.Q:
            self.lir.add(x)
            S[x] = True
        elif x in S:
            del self.nonres[x]
            S.move_to_end(x)
            self.lir.add(x)
            self._demote()
        else:
            S[x] = True
            self.Q[x] = True
        return False


class Cache:
    """Follow the leader: shadow-simulate several policies, evict what the
    recently best one has evicted."""

    def __init__(self, capacity, horizon=8.0, margin=6.0):
        self.capacity = capacity
        self.store = {}
        self.pols = [LIRS(capacity, ghost=6.0), ARC(capacity)]
        self.score = [0.0] * len(self.pols)
        self.decay = 1.0 - 1.0 / (horizon * capacity)
        self.margin = margin
        self.lead = 0
        self.diff = {}

    def access(self, key):
        d = self.decay
        sc = self.score
        for i, p in enumerate(self.pols):
            sc[i] = sc[i] * d + p.access(key)
        best = 0
        for i in range(1, len(sc)):
            if sc[i] > sc[best]:
                best = i
        lead = self.pols[self.lead]
        if best != self.lead and sc[best] > sc[self.lead] + self.margin:
            self.lead = best
            lead = self.pols[best]
            lead.ev.clear()
            ls = lead.store
            self.diff = {k: True for k in self.store if k not in ls}
        else:
            for k in lead.ev:
                if k in self.store:
                    self.diff[k] = True
            lead.ev.clear()
        for p in self.pols:
            if p is not lead:
                p.ev.clear()
        self.diff.pop(key, None)
        if key in self.store:
            return True
        self.store[key] = True
        if len(self.store) > self.capacity:
            ls = lead.store
            while True:
                k = next(iter(self.diff))
                del self.diff[k]
                if k in self.store and k not in ls:
                    del self.store[k]
                    break
        return False
