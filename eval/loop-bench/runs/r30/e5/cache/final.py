from collections import OrderedDict


class ARC:
    def __init__(self, c):
        self.c = c
        self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = set()
        self.ev = []

    def _replace(self, in_b2):
        t1 = self.t1
        if t1 and (len(t1) > self.p or (in_b2 and len(t1) == self.p)):
            k, _ = t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        self.store.discard(k); self.ev.append(k)

    def access(self, key):
        c = self.c
        if key in self.t1:
            del self.t1[key]; self.t2[key] = True; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p = min(c, self.p + max(1, len(self.b2) // max(1, len(self.b1))))
            self._replace(False)
            del self.b1[key]; self.t2[key] = True; self.store.add(key); return False
        if key in self.b2:
            self.p = max(0, self.p - max(1, len(self.b1) // max(1, len(self.b2))))
            self._replace(True)
            del self.b2[key]; self.t2[key] = True; self.store.add(key); return False
        if len(self.t1) + len(self.b1) >= c:
            if len(self.t1) < c:
                self.b1.popitem(last=False); self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False); self.store.discard(k); self.ev.append(k)
        else:
            tot = len(self.t1) + len(self.t2) + len(self.b1) + len(self.b2)
            if tot >= c:
                if tot >= 2 * c: self.b2.popitem(last=False)
                if len(self.t1) + len(self.t2) >= c: self._replace(False)
        self.t1[key] = True; self.store.add(key); return False


class WTL:
    def __init__(self, cap, win=0.05, prot=0.8, samp=10):
        self.cap = cap
        self.wmax = max(1, int(cap * win))
        self.mmax = cap - self.wmax
        self.pmax = int(self.mmax * prot)
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.freq = {}
        self.n = 0
        self.sample = samp * cap
        self.store = set()
        self.ev = []

    def access(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.n += 1
        if self.n >= self.sample:
            self.n = 0
            self.freq = {k: v >> 1 for k, v in f.items() if v > 1}
        if key in self.prot:
            self.prot.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key] = True
            if len(self.prot) > self.pmax:
                k, _ = self.prot.popitem(last=False); self.prob[k] = True
            return True
        if key in self.win:
            self.win.move_to_end(key); return True
        self.win[key] = True; self.store.add(key)
        if len(self.win) > self.wmax:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mmax:
                self.prob[cand] = True
            else:
                vic = next(iter(self.prob)) if self.prob else next(iter(self.prot))
                if self.freq.get(cand, 0) > self.freq.get(vic, 0):
                    if self.prob: del self.prob[vic]
                    else: del self.prot[vic]
                    self.store.discard(vic); self.ev.append(vic); self.prob[cand] = True
                else:
                    self.store.discard(cand); self.ev.append(cand)
        return False


class Cache:
    HYST = 0.02

    def __init__(self, capacity):
        self.cap = capacity
        self.ex = [WTL(capacity, 0.05), ARC(capacity), WTL(capacity, 0.01, 0.5, 4), WTL(capacity, 0.3, 0.8, 20), WTL(capacity, 0.02, 0.9, 60), WTL(capacity, 0.1, 0.8, 3)]
        n = len(self.ex)
        self.score = [0.0] * n
        self.decay = 1.0 - 1.0 / (self.HORIZON * capacity)
        self.lead = 0
        self.stale = set()
        self.store = set()

    HORIZON = 5

    def access(self, key):
        ex = self.ex; sc = self.score; d = self.decay
        for i, e in enumerate(ex):
            h = e.access(key)
            sc[i] = sc[i] * d + (1.0 if h else 0.0)
        best = self.lead
        for i in range(len(ex)):
            if sc[i] > sc[best] + self.HYST * (1.0 / (1.0 - d)):
                best = i
        L = ex[best]
        if best != self.lead:
            self.lead = best
            self.stale = self.store - L.store
        real = self.store
        stale = self.stale
        for k in L.ev:
            real.discard(k); stale.discard(k)
        for e in ex:
            e.ev.clear()
        if key in real:
            return True
        if key in L.store:
            real.add(key)
            if len(real) > self.cap:
                real.discard(stale.pop())
        return False
