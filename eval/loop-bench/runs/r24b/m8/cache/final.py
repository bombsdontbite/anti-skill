from collections import OrderedDict


class Lirs:
    """Plain LIRS, used only as a shadow to judge whether a small HIR share is paying off."""

    def __init__(self, capacity, h, owner=None):
        self.owner = owner
        self.cap = capacity
        self.lcap = capacity - max(1, int(h))
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.lir = set()
        self.store = set()
        self.nonres_max = capacity * 3
        self.nonres = 0

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if k in self.lir:
                break
            del S[k]
            if k not in self.store:
                self.nonres -= 1

    def _ok(self, key):
        if self.owner is None:
            return True
        f = self.owner.freq
        return f.get(key, 0) >= f.get(next(iter(self.S)), 0)

    def access(self, key):
        S, Q, lir, store = self.S, self.Q, self.lir, self.store
        if key in lir:
            S.move_to_end(key)
            self._prune()
            return True
        if key in store:
            if key in S and self._ok(key):
                S.move_to_end(key)
                del Q[key]
                lir.add(key)
                k, _ = S.popitem(last=False)
                lir.discard(k)
                Q[k] = True
                self._prune()
            else:
                S[key] = True
                S.move_to_end(key)
                Q.move_to_end(key)
            return True
        if len(lir) < self.lcap:
            store.add(key)
            if key in S:
                self.nonres -= 1
            S[key] = True
            S.move_to_end(key)
            lir.add(key)
            return False
        if len(store) >= self.cap:
            k, _ = Q.popitem(last=False)
            store.discard(k)
            if k in S:
                self.nonres += 1
        store.add(key)
        if key in S and self._ok(key):
            self.nonres -= 1
            S.move_to_end(key)
            lir.add(key)
            k, _ = S.popitem(last=False)
            lir.discard(k)
            Q[k] = True
            self._prune()
        elif key in S:
            self.nonres -= 1
            S.move_to_end(key)
            Q[key] = True
        else:
            S[key] = True
            Q[key] = True
        while self.nonres > self.nonres_max:
            for k in S:
                if k not in store:
                    del S[k]
                    self.nonres -= 1
                    break
        return False


class Cache:
    """LIRS whose resident-HIR share switches between small and large, depending on whether
    a shadow LRU or a shadow small-HIR LIRS has been hitting more lately."""
    HIR = 0.01
    HBIG = 0.5
    RATE = 0.002
    THR = 0.01
    STEP = 0.05
    NONRES = 3
    FREQ = True
    FRATE = 0.0005
    FTHR = 0.0
    AGE = 40
    M = 1
    C = 0

    def __init__(self, capacity):
        self.cap = capacity
        self.h0 = max(1.0, capacity * self.HIR)
        self.h = self.h0
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.lir = set()
        self.store = set()
        self.nonres_max = capacity * self.NONRES
        self.nonres = 0
        self.score = 0.0
        self.lru = OrderedDict()
        self.lirs = Lirs(capacity, self.h0)
        self.freq = {}
        self.ops = 0
        self.flirs = Lirs(capacity, self.h0, self)
        self.fscore = 0.0
        self.use_freq = False

    def _prune(self):
        S, lir = self.S, self.lir
        while S:
            k = next(iter(S))
            if k in lir:
                break
            del S[k]
            if k not in self.store:
                self.nonres -= 1

    def _demote_bottom(self):
        k, _ = self.S.popitem(last=False)
        self.lir.discard(k)
        self.Q[k] = True
        self._prune()

    def _balance(self):
        while self.lir and len(self.lir) > self.cap - int(self.h):
            self._demote_bottom()

    def _promote_ok(self, key):
        if not self.use_freq or len(self.lir) < self.cap - int(self.h):
            return True
        f = self.freq
        return f.get(key, 0) * self.M + self.C >= f.get(next(iter(self.S)), 0)

    def access(self, key):
        lru = self.lru
        if key in lru:
            lru.move_to_end(key)
            d = 1.0
        else:
            if len(lru) >= self.cap:
                lru.popitem(last=False)
            lru[key] = True
            d = 0.0
        base = self.lirs.access(key)
        if base:
            d -= 1.0
        self.score += (d - self.score) * self.RATE
        target = self.cap * self.HBIG if self.score > self.THR else self.h0
        self.h += (target - self.h) * self.STEP
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.cap * self.AGE:
            self.ops = 0
            self.freq = {k: v >> 1 for k, v in f.items() if v > 1}
        fd = self.flirs.access(key) - base
        self.fscore += (fd - self.fscore) * self.FRATE
        self.use_freq = self.FREQ and self.fscore > self.FTHR
        return self._access(key)

    def _access(self, key):
        S, Q, lir, store = self.S, self.Q, self.lir, self.store
        if key in lir:
            S.move_to_end(key)
            self._prune()
            return True
        if key in store:
            if key in S and self._promote_ok(key):
                S.move_to_end(key)
                del Q[key]
                lir.add(key)
                self._balance()
                self._prune()
            else:
                S[key] = True
                S.move_to_end(key)
                Q.move_to_end(key)
            return True
        if len(lir) < self.cap - int(self.h) and len(store) < self.cap:
            store.add(key)
            if key in S:
                self.nonres -= 1
            S[key] = True
            S.move_to_end(key)
            lir.add(key)
            return False
        if len(store) >= self.cap:
            if not Q:
                self._demote_bottom()
            k, _ = Q.popitem(last=False)
            store.discard(k)
            if k in S:
                self.nonres += 1
        store.add(key)
        if key in S:
            self.nonres -= 1
            S.move_to_end(key)
            if self._promote_ok(key):
                lir.add(key)
            else:
                Q[key] = True
        else:
            S[key] = True
            Q[key] = True
        self._balance()
        self._prune()
        while self.nonres > self.nonres_max:
            for k in S:
                if k not in store:
                    del S[k]
                    self.nonres -= 1
                    break
            self._prune()
        return False
