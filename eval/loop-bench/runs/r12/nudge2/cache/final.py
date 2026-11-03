from collections import OrderedDict


class _Seg:
    """W-TinyLFU over a shared frequency table; wmax may change at any time."""

    def __init__(self, capacity, wmax, prot):
        self.capacity = capacity
        self.wmax = wmax
        self.protfrac = prot
        self.store = {}
        self.win = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()

    def access(self, key, freq):
        store = self.store
        if key in store:
            if key in self.win:
                self.win.move_to_end(key)
            elif key in self.prot:
                self.prot.move_to_end(key)
            else:
                del self.prob[key]
                self.prot[key] = True
                pmax = int((self.capacity - self.wmax) * self.protfrac)
                while len(self.prot) > pmax:
                    k, _ = self.prot.popitem(last=False)
                    self.prob[k] = True
            return True
        store[key] = True
        win = self.win
        win[key] = True
        while len(win) > self.wmax:
            cand, _ = win.popitem(last=False)
            if len(store) <= self.capacity:
                self.prob[cand] = True
                continue
            src = self.prob if self.prob else self.prot
            if not src:
                win[cand] = True
                win.move_to_end(cand, last=False)
                break
            vic = next(iter(src))
            if freq.get(cand, 0) > freq.get(vic, 0):
                del src[vic]
                del store[vic]
                self.prob[cand] = True
            else:
                del store[cand]
        while len(store) > self.capacity:
            if self.prob:
                k, _ = self.prob.popitem(last=False)
            elif self.prot:
                k, _ = self.prot.popitem(last=False)
            else:
                k, _ = win.popitem(last=False)
            del store[k]
        return False


class _Freq:
    def __init__(self, period):
        self.f = {}
        self.ops = 0
        self.period = period

    def add(self, key):
        f = self.f
        v = f.get(key, 0)
        if v < 15:
            f[key] = v + 1
        self.ops += 1
        if self.ops >= self.period:
            self.ops = 0
            self.f = {k: v >> 1 for k, v in f.items() if v > 1}


class _Lirs:
    def __init__(self, capacity, hir):
        self.capacity = capacity
        self.store = {}
        self.lmax = capacity - max(1, int(capacity * hir))
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.lir = set()

    def _prune(self):
        S = self.S
        lir = self.lir
        while S:
            k = next(iter(S))
            if k in lir:
                break
            del S[k]

    def _demote(self):
        S = self.S
        k, _ = S.popitem(last=False)
        self.lir.discard(k)
        self.Q[k] = True
        self._prune()

    def access(self, key):
        S = self.S
        Q = self.Q
        lir = self.lir
        store = self.store
        if key in lir:
            S[key] = True
            S.move_to_end(key)
            self._prune()
            return True
        if key in store:
            if key in S:
                S.move_to_end(key)
                del Q[key]
                lir.add(key)
                self._demote()
            else:
                S[key] = True
                Q.move_to_end(key)
            return True
        if len(store) >= self.capacity:
            k, _ = Q.popitem(last=False)
            del store[k]
        store[key] = True
        if len(lir) < self.lmax:
            lir.add(key)
            S[key] = True
            S.move_to_end(key)
            return False
        if key in S:
            S.move_to_end(key)
            lir.add(key)
            self._demote()
        else:
            S[key] = True
            Q[key] = True
        return False


class _Tlfu:
    def __init__(self, seg, fr):
        self.seg = seg
        self.fr = fr
        self.store = seg.store

    def access(self, key):
        return self.seg.access(key, self.fr.f)


class Cache:
    """Follows whichever of several shadow policies (W-TinyLFU variants, LIRS) has the most recent hits."""

    FRACS = (0.01, 0.2, 0.99)
    SAMPLES = (3, 30)
    HIRS = (0.01, 0.1)
    HALF = 25
    PROT = 0.8
    MARGIN = 0.02

    def __init__(self, capacity):
        self.capacity = capacity
        wins = sorted({max(1, min(capacity - 1, int(capacity * f))) for f in self.FRACS})
        self.freqs = [_Freq(s * capacity) for s in self.SAMPLES]
        self.shadows = [_Tlfu(_Seg(capacity, w, self.PROT), fr) for fr in self.freqs for w in wins]
        self.shadows += [_Lirs(capacity, h) for h in self.HIRS]
        self.scores = [0.0] * len(self.shadows)
        self.decay = 1.0 - 1.0 / (self.HALF * capacity)
        self.store = OrderedDict()
        self.lead = self.shadows[0]
        self.li = 0
        self.tick = 0

    def access(self, key):
        for fr in self.freqs:
            fr.add(key)
        d = self.decay
        sc = self.scores
        for i, s in enumerate(self.shadows):
            sc[i] = sc[i] * d + s.access(key)
        self.tick += 1
        if self.tick >= 64:
            self.tick = 0
            best = 0
            for i in range(1, len(sc)):
                if sc[i] > sc[best]:
                    best = i
            if sc[best] > sc[self.li] * (1.0 + self.MARGIN):
                self.li = best
                self.lead = self.shadows[best]
        store = self.store
        if key in store:
            store.move_to_end(key)
            return True
        if len(store) < self.capacity:
            store[key] = True
            return False
        lead = self.lead.store
        if key not in lead:
            return False
        for k in store:
            if k not in lead:
                break
        del store[k]
        store[key] = True
        return False
