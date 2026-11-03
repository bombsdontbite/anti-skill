from collections import OrderedDict
import random


class LRU:
    def __init__(self, c):
        self.c = c
        self.store = OrderedDict()

    def access(self, k):
        s = self.store
        if k in s:
            s.move_to_end(k)
            return True
        if len(s) >= self.c:
            s.popitem(last=False)
        s[k] = True
        return False


class BIP:
    def __init__(self, c, eps=32):
        self.c = c
        self.store = OrderedDict()
        self.n = 0
        self.eps = eps

    def access(self, k):
        s = self.store
        if k in s:
            s.move_to_end(k)
            return True
        if len(s) >= self.c:
            s.popitem(last=False)
        s[k] = True
        self.n += 1
        if self.n % self.eps:
            s.move_to_end(k, last=False)
        return False


class ARC:
    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1 = OrderedDict()
        self.t2 = OrderedDict()
        self.b1 = OrderedDict()
        self.b2 = OrderedDict()
        self.store = set()

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
            self.p = min(c, self.p + max(1, len(self.b2) // max(1, len(self.b1))))
            self._replace(False)
            del self.b1[key]
            self.t2[key] = True
            self.store.add(key)
            return False
        if key in self.b2:
            self.p = max(0, self.p - max(1, len(self.b1) // max(1, len(self.b2))))
            self._replace(True)
            del self.b2[key]
            self.t2[key] = True
            self.store.add(key)
            return False
        l1 = len(self.t1) + len(self.b1)
        if l1 == c:
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


class Tiny:
    def __init__(self, capacity, wfrac=100, age=10):
        self.cap = capacity
        self.wcap = max(1, capacity // wfrac)
        self.win = OrderedDict()
        self.main = OrderedDict()
        self.store = set()
        self.freq = {}
        self.n = 0
        self.sample = capacity * age

    def access(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.n += 1
        if self.n >= self.sample:
            self.n = 0
            self.freq = f = {k: v >> 1 for k, v in f.items() if v > 1}
        if key in self.main:
            self.main.move_to_end(key)
            return True
        if key in self.win:
            self.win.move_to_end(key)
            return True
        self.win[key] = True
        self.store.add(key)
        if len(self.win) > self.wcap:
            k, _ = self.win.popitem(last=False)
            if len(self.main) + len(self.win) < self.cap:
                self.main[k] = True
            else:
                v = next(iter(self.main))
                if f.get(k, 0) > f.get(v, 0):
                    del self.main[v]
                    self.store.discard(v)
                    self.main[k] = True
                else:
                    self.store.discard(k)
        return False


class LIRS:
    def __init__(self, capacity, hfrac=100):
        self.cap = capacity
        self.hir = max(1, capacity // hfrac)
        self.llirs = capacity - self.hir
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.st = {}
        self.nl = 0
        self.store = set()

    def _prune(self):
        S, st = self.S, self.st
        while S:
            k = next(iter(S))
            if st[k] == 1:
                break
            del S[k]
            if st[k] == 2:
                del st[k]

    def _demote(self):
        S, st = self.S, self.st
        k = next(iter(S))
        del S[k]
        st[k] = 0
        self.Q[k] = True
        self.nl -= 1
        self._prune()

    def access(self, key):
        S, Q, st = self.S, self.Q, self.st
        s = st.get(key)
        if s == 1:
            S.move_to_end(key)
            self._prune()
            return True
        if s == 0:
            if key in S:
                S.move_to_end(key)
                st[key] = 1
                del Q[key]
                self.nl += 1
                self._demote()
            else:
                S[key] = True
                Q.move_to_end(key)
            return True
        if len(self.store) >= self.cap:
            v, _ = Q.popitem(last=False)
            self.store.discard(v)
            if v in S:
                st[v] = 2
            else:
                del st[v]
        self.store.add(key)
        if s == 2:
            S.move_to_end(key)
            st[key] = 1
            self.nl += 1
            self._demote()
        elif self.nl < self.llirs:
            st[key] = 1
            S[key] = True
            self.nl += 1
        else:
            st[key] = 0
            S[key] = True
            Q[key] = True
        if len(S) > 3 * self.cap:
            for k in list(S):
                if st[k] == 2:
                    del S[k]
                    del st[k]
                    if len(S) <= 2 * self.cap:
                        break
        return False


class Cache:
    DECAY = 0.996
    MARGIN = 1.0
    NAMES = "LRU,LIRS"

    def __init__(self, capacity):
        self.cap = capacity
        mk = {"LRU": LRU, "ARC": ARC, "BIP": BIP, "LIRS": LIRS, "TINY": Tiny}
        self.pols = [mk[n](capacity) for n in self.NAMES.split(",")]
        self.score = [0.0] * len(self.pols)
        self.lead = len(self.pols) - 1
        self.order = OrderedDict()
        self.store = self.order

    def access(self, key):
        d = self.DECAY
        sc = self.score
        for i, p in enumerate(self.pols):
            sc[i] = sc[i] * d + (1.0 if p.access(key) else 0.0)
        best = self.lead
        for i in range(len(sc)):
            if sc[i] > sc[best] + self.MARGIN:
                best = i
        self.lead = best
        o = self.order
        if key in o:
            o.move_to_end(key)
            return True
        ls = self.pols[best].store
        if len(o) >= self.cap:
            victim = None
            for k in o:
                if k not in ls:
                    victim = k
                    break
            if victim is None:
                victim = next(iter(o))
            del o[victim]
        o[key] = True
        return False
