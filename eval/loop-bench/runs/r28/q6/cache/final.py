from collections import OrderedDict, deque

FRACS = (0.01, 0.1, 0.3, 0.6, 0.99)
RESETS = (3, 10, 40)


class WTinyLFU:
    def __init__(self, capacity, wcap, pfrac=0.8, k=1, tie=0):
        self.capacity = capacity
        self.pfrac = pfrac
        self.k = k
        self.tie = tie
        self.tmin = 2
        self.tc = 0
        self.store = {}
        self.wcap = wcap
        self.window = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.score = 0.0
        self.ev = []

    def resize(self, wcap):
        self.wcap = wcap
        while len(self.window) > wcap:
            k, _ = self.window.popitem(last=False)
            self.prob[k] = True
            self.prob.move_to_end(k, last=False)
        mcap = self.capacity - wcap
        while len(self.prob) + len(self.prot) > mcap:
            src = self.prob if self.prob else self.prot
            k, _ = src.popitem(last=False)
            del self.store[k]
            self.ev.append(k)

    def access(self, key, f):
        if key in self.store:
            if key in self.window:
                self.window.move_to_end(key)
            elif key in self.prot:
                self.prot.move_to_end(key)
            else:
                del self.prob[key]
                self.prot[key] = True
                if len(self.prot) > int((self.capacity - self.wcap) * self.pfrac):
                    k, _ = self.prot.popitem(last=False)
                    self.prob[k] = True
            return True
        self.store[key] = True
        self.window[key] = True
        if len(self.window) > self.wcap:
            cand, _ = self.window.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.capacity - self.wcap:
                self.prob[cand] = True
                return False
            src = self.prob if self.prob else self.prot
            if self.k == 1:
                victim = next(iter(src))
            else:
                it = iter(src)
                victim = next(it)
                fv = f.get(victim, 0)
                for _ in range(self.k - 1):
                    k2 = next(it, None)
                    if k2 is None:
                        break
                    if f.get(k2, 0) < fv:
                        victim, fv = k2, f.get(k2, 0)
            fc = f.get(cand, 0)
            fv = f.get(victim, 0)
            admit = fc > fv
            if not admit and self.tie and fc == fv and fc >= self.tmin:
                self.tc += 1
                if self.tc >= self.tie:
                    self.tc = 0
                    admit = True
            if admit:
                del src[victim]
                del self.store[victim]
                self.ev.append(victim)
                self.prob[cand] = True
            else:
                del self.store[cand]
                self.ev.append(cand)
        return False


class Freq:
    def __init__(self, reset):
        self.f = {}
        self.ops = 0
        self.reset = reset

    def add(self, key):
        f = self.f
        f[key] = min(15, f.get(key, 0) + 1)
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.f = {a: b >> 1 for a, b in f.items() if b > 1}


class ARC:
    

    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = {}
        self.score = 0.0
        self.ev = []

    def _replace(self, inb2):
        if self.t1 and (len(self.t1) > self.p or (inb2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        del self.store[k]; self.ev.append(k)

    def access(self, x, f):
        c = self.c
        if x in self.t1:
            del self.t1[x]; self.t2[x] = True; return True
        if x in self.t2:
            self.t2.move_to_end(x); return True
        if x in self.b1:
            self.p = min(c, self.p + max(len(self.b2) // max(1, len(self.b1)), 1))
            self._replace(False); del self.b1[x]; self.t2[x] = True; self.store[x] = True
            return False
        if x in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // max(1, len(self.b2)), 1))
            self._replace(True); del self.b2[x]; self.t2[x] = True; self.store[x] = True
            return False
        l1 = len(self.t1) + len(self.b1)
        if l1 == c:
            if len(self.t1) < c:
                self.b1.popitem(last=False); self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False); del self.store[k]; self.ev.append(k)
        elif l1 < c:
            tot = l1 + len(self.t2) + len(self.b2)
            if tot >= c:
                if tot == 2 * c:
                    self.b2.popitem(last=False)
                self._replace(False)
        self.t1[x] = True; self.store[x] = True
        return False


class S3:
    

    def __init__(self, capacity):
        self.capacity = capacity
        self.scap = max(1, capacity // 10)
        self.mcap = capacity - self.scap
        self.small = deque(); self.main = deque()
        self.freq = {}
        self.ghost = OrderedDict()
        self.store = {}
        self.score = 0.0
        self.ev = []
        self.ns = 0

    def _evict(self):
        while True:
            if self.ns >= self.scap or not self.main:
                k = self.small.popleft(); self.ns -= 1
                if self.freq[k] > 0:
                    self.freq[k] = 0; self.main.append(k)
                else:
                    del self.store[k]; del self.freq[k]; self.ev.append(k)
                    self.ghost[k] = True
                    if len(self.ghost) > self.mcap: self.ghost.popitem(last=False)
                    return
            else:
                k = self.main.popleft()
                if self.freq[k] > 0:
                    self.freq[k] -= 1; self.main.append(k)
                else:
                    del self.store[k]; del self.freq[k]; self.ev.append(k); return

    def access(self, key, f):
        if key in self.store:
            if self.freq[key] < 3: self.freq[key] += 1
            return True
        if len(self.store) >= self.capacity: self._evict()
        self.store[key] = True; self.freq[key] = 0
        if key in self.ghost:
            del self.ghost[key]; self.main.append(key)
        else:
            self.small.append(key); self.ns += 1
        return False


class BIP:
    def __init__(self, capacity, every=32):
        self.capacity = capacity
        self.store = OrderedDict()
        self.every = every
        self.c = 0
        self.score = 0.0
        self.ev = []

    def access(self, key, f):
        store = self.store
        if key in store:
            store.move_to_end(key)
            return True
        if len(store) >= self.capacity:
            k, _ = store.popitem(last=False)
            self.ev.append(k)
        store[key] = True
        self.c += 1
        if self.c >= self.every:
            self.c = 0
        else:
            store.move_to_end(key, last=False)
        return False


class Cache:
    """Follows the best of a grid of W-TinyLFU shadow simulations (window size x frequency
    history): admits what the leader holds, and evicts first what the leader has dropped."""

    def __init__(self, capacity, period_mult=2.0, decay=0.9, fracs=FRACS, resets=RESETS, extra=True):
        self.capacity = capacity
        caps = sorted({min(capacity - 1, max(1, int(capacity * fr))) for fr in fracs})
        self.freqs = [Freq(capacity * r) for r in resets]
        self.shadows = [(WTinyLFU(capacity, w), i) for i in range(len(resets)) for w in caps]
        if extra:
            self.shadows += [(ARC(capacity), 0), (S3(capacity), 0), (BIP(capacity), 0), (BIP(capacity, 8), 0)]
        self.best = self.shadows[0][0]
        self.store = {}
        self.dropped = OrderedDict()
        self.period = max(1, int(capacity * period_mult))
        self.n = 0
        self.decay = decay

    def access(self, key):
        store = self.store
        hit = key in store
        fs = self.freqs
        for q in fs:
            q.add(key)
        for s, i in self.shadows:
            s.ev = []
            if s.access(key, fs[i].f):
                s.score += 1
        best = self.best
        dropped = self.dropped
        for k in best.ev:
            if k in store:
                dropped[k] = True
        self.n += 1
        if self.n >= self.period:
            self.n = 0
            nb = max(self.shadows, key=lambda t: t[0].score)[0]
            for s, _ in self.shadows:
                s.score *= self.decay
            if nb is not best:
                self.best = best = nb
                bs = best.store
                dropped.clear()
                for k in store:
                    if k not in bs:
                        dropped[k] = True
        if key in best.store:
            dropped.pop(key, None)
            if not hit:
                if len(store) >= self.capacity:
                    if dropped:
                        k, _ = dropped.popitem(last=False)
                    else:
                        k = next(iter(store))
                    del store[k]
                store[key] = True
        return hit
