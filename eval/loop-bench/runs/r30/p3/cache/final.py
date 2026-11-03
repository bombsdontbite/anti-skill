from collections import OrderedDict

NONRES_MULT = 2


class ARC:
    def __init__(self, capacity):
        self.c = capacity
        self.store = set()
        self.t1 = OrderedDict()
        self.t2 = OrderedDict()
        self.b1 = OrderedDict()
        self.b2 = OrderedDict()
        self.p = 0

    def _replace(self, in_b2):
        t1, t2 = self.t1, self.t2
        if t1 and (len(t1) > self.p or (in_b2 and len(t1) == self.p)):
            k, _ = t1.popitem(last=False)
            self.b1[k] = True
        else:
            k, _ = t2.popitem(last=False)
            self.b2[k] = True
        self.store.discard(k)

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
            self.store.add(key)
            return False
        if key in self.b2:
            self.p = max(0, self.p - max(1, len(self.b1) // len(self.b2)))
            self._replace(True)
            del self.b2[key]
            self.t2[key] = True
            self.store.add(key)
            return False
        l1 = len(self.t1) + len(self.b1)
        if l1 >= c:
            if len(self.t1) < c:
                self.b1.popitem(last=False)
                self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False)
                self.store.discard(k)
        else:
            tot = l1 + len(self.t2) + len(self.b2)
            if tot >= c:
                if tot >= 2 * c:
                    self.b2.popitem(last=False)
                if len(self.t1) + len(self.t2) >= c:
                    self._replace(False)
        self.t1[key] = True
        self.store.add(key)
        return False




class LIRS:
    def __init__(self, capacity, HIR_FRAC):
        self.c = capacity
        self.store = set()
        self.lir_cap = max(1, min(capacity - 1, capacity - max(1, int(capacity * HIR_FRAC))))
        self.S = OrderedDict()  # key -> 0 LIR, 1 resident HIR, 2 nonresident
        self.Q = OrderedDict()
        self.nonres = OrderedDict()
        self.nlir = 0

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            st = S[k]
            if st == 0:
                break
            del S[k]
            if st == 2:
                del self.nonres[k]

    def _demote_bottom(self):
        S = self.S
        k = next(iter(S))
        del S[k]
        self.nlir -= 1
        self.Q[k] = True
        # state 1 but not in S now
        self._prune()

    def access(self, key):
        S, Q = self.S, self.Q
        st = S.get(key)
        if key in self.store:
            if st == 0:
                bottom = next(iter(S)) == key
                S.move_to_end(key)
                if bottom:
                    self._prune()
            elif st == 1:
                del Q[key]
                S[key] = 0
                S.move_to_end(key)
                self.nlir += 1
                self._demote_bottom()
            else:
                Q.move_to_end(key)
                S[key] = 1
            return True
        if len(self.store) >= self.c:
            k, _ = Q.popitem(last=False)
            self.store.discard(k)
            if k in S:
                S[k] = 2
                self.nonres[k] = True
                if len(self.nonres) > NONRES_MULT * self.c:
                    old, _ = self.nonres.popitem(last=False)
                    del S[old]
        self.store.add(key)
        st = S.get(key)
        if st == 2:
            del self.nonres[key]
            S[key] = 0
            S.move_to_end(key)
            self.nlir += 1
            self._demote_bottom()
        elif self.nlir < self.lir_cap:
            S[key] = 0
            self.nlir += 1
        else:
            S[key] = 1
            Q[key] = True
        return False


DECAY = 0.9995
MARGIN = 3.0


class Cache:
    def __init__(self, capacity):
        self.c = capacity
        self.store = set()
        self.order = OrderedDict()
        self.sh = [LIRS(capacity, 0.01), LIRS(capacity, 0.04), LIRS(capacity, 0.15), ARC(capacity)]
        self.score = [0.0] * len(self.sh)
        self.lead = 0

    def access(self, key):
        sc = self.score
        for i, s in enumerate(self.sh):
            sc[i] = sc[i] * DECAY + (1.0 if s.access(key) else 0.0)
        best = max(range(len(sc)), key=sc.__getitem__)
        if sc[best] > sc[self.lead] + MARGIN:
            self.lead = best
        L = self.sh[self.lead].store
        store, order = self.store, self.order
        if key in store:
            order.move_to_end(key)
            return True
        if len(store) >= self.c:
            diff = store - L
            if diff:
                victim = next(iter(diff))
            else:
                victim = next(iter(order))
            del order[victim]
            store.discard(victim)
        store.add(key)
        order[key] = True
        return False
