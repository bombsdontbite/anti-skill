from collections import OrderedDict


class _Freq:
    def __init__(self, reset, cap):
        self.f = {}
        self.ops = 0
        self.reset = reset
        self.cap = cap

    def add(self, key):
        f = self.f
        v = f.get(key, 0)
        if v < self.cap:
            f[key] = v + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.f = {k: v >> 1 for k, v in f.items() if v > 1}
            self.ops = 0


class _WTLFU:
    PROT = 0.8

    def __init__(self, capacity, wmax, freq):
        self.capacity = capacity
        self.wmax = wmax
        self.mmax = capacity - wmax
        self.pmax = self.mmax * self.PROT
        self.fq = freq
        self.store = {}
        self.window = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()

    def access(self, key):
        if key in self.store:
            if key in self.window:
                self.window.move_to_end(key)
            elif key in self.prot:
                self.prot.move_to_end(key)
            else:
                del self.prob[key]
                self.prot[key] = True
                if len(self.prot) > self.pmax:
                    k, _ = self.prot.popitem(last=False)
                    self.prob[k] = True
            return True
        self.store[key] = True
        self.window[key] = True
        if len(self.window) > self.wmax:
            cand, _ = self.window.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mmax:
                self.prob[cand] = True
                return False
            src = self.prob if self.prob else self.prot
            victim = next(iter(src))
            freq = self.fq.f
            if freq.get(cand, 0) > freq.get(victim, 0):
                del src[victim]
                del self.store[victim]
                self.prob[cand] = True
            else:
                del self.store[cand]
        return False


class _LRU:
    def __init__(self, capacity):
        self.capacity = capacity
        self.store = OrderedDict()

    def access(self, key):
        if key in self.store:
            self.store.move_to_end(key)
            return True
        if len(self.store) >= self.capacity:
            self.store.popitem(last=False)
        self.store[key] = True
        return False


class _BIP:
    """LRU that inserts most new keys at the LRU end."""

    def __init__(self, capacity, every):
        self.capacity = capacity
        self.store = OrderedDict()
        self.every = every
        self.n = 0

    def access(self, key):
        store = self.store
        if key in store:
            store.move_to_end(key)
            return True
        if len(store) >= self.capacity:
            store.popitem(last=False)
        store[key] = True
        self.n += 1
        if self.n < self.every:
            store.move_to_end(key, last=False)
        else:
            self.n = 0
        return False


class _LIRS:
    def __init__(self, capacity, hfrac=0.01, ghost=3):
        self.capacity = capacity
        self.hmax = max(1, int(capacity * hfrac))
        self.lmax = capacity - self.hmax
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.lir = set()
        self.store = {}
        self.smax = ghost * capacity

    def _prune(self):
        S = self.S
        lir = self.lir
        while S:
            k = next(iter(S))
            if k in lir:
                break
            del S[k]

    def _demote(self):
        k, _ = self.S.popitem(last=False)
        self.lir.discard(k)
        self.Q[k] = True
        self._prune()

    def access(self, key):
        S = self.S
        lir = self.lir
        if key in self.store:
            if key in lir:
                S[key] = True
                S.move_to_end(key)
                self._prune()
            elif key in S:
                S.move_to_end(key)
                del self.Q[key]
                lir.add(key)
                self._demote()
            else:
                S[key] = True
                self.Q.move_to_end(key)
            return True
        if len(self.store) >= self.capacity:
            k, _ = self.Q.popitem(last=False)
            del self.store[k]
        self.store[key] = True
        if len(lir) < self.lmax:
            lir.add(key)
            S[key] = True
            S.move_to_end(key)
        elif key in S:
            S.move_to_end(key)
            lir.add(key)
            self._demote()
        else:
            S[key] = True
            self.Q[key] = True
        if len(S) > self.smax:
            store = self.store
            n = len(S) - self.smax // 2
            for k in list(S):
                if n <= 0:
                    break
                if k not in store:
                    del S[k]
                    n -= 1
        return False


class Cache:
    """Mirrors the best of several shadow policies (LIRS, W-TinyLFU, LRU, BIP).

    The cache follows a leader's contents; it switches leader only when the
    recent hit advantage outweighs the keys it would have to replace.
    """

    LIRS = (0.01, 0.1, 0.3)
    WINS = (0.01,)
    SAMPLES = (10, 3)
    BIPS = (8,)
    CAP = 15
    DECAY = 0.9
    MARGIN = 0.1
    COST = 1.0

    def __init__(self, capacity):
        self.capacity = capacity
        self.shadows = [_LIRS(capacity, h) for h in self.LIRS]
        self.freqs = [_Freq(s * capacity, self.CAP) for s in self.SAMPLES]
        for fq in self.freqs:
            for f in self.WINS:
                w = min(capacity - 1, max(1, int(capacity * f)))
                self.shadows.append(_WTLFU(capacity, w, fq))
        self.shadows.append(_LRU(capacity))
        for e in self.BIPS:
            self.shadows.append(_BIP(capacity, e))
        self.score = [0.0] * len(self.shadows)
        self.lead = 0
        self.store = OrderedDict()
        self.n = 0

    def access(self, key):
        for fq in self.freqs:
            fq.add(key)
        score = self.score
        for i, s in enumerate(self.shadows):
            if s.access(key):
                score[i] += 1
        self.n += 1
        if self.n >= self.capacity:
            self.n = 0
            best = self.lead
            for i in range(len(score)):
                if score[i] > score[best]:
                    best = i
            gain = score[best] - score[self.lead]
            if gain > self.MARGIN * self.capacity:
                bs = self.shadows[best].store
                diff = 0
                for k in self.store:
                    if k not in bs:
                        diff += 1
                if gain > self.COST * diff:
                    self.lead = best
            d = self.DECAY
            self.score = [x * d for x in score]
        store = self.store
        if key in store:
            store.move_to_end(key)
            return True
        ls = self.shadows[self.lead].store
        if key not in ls and len(store) >= self.capacity:
            return False
        if len(store) >= self.capacity:
            for k in store:
                if k not in ls:
                    break
            del store[k]
        store[key] = True
        return False
