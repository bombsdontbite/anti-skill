from collections import OrderedDict


class _TL:
    def __init__(self, c, w, f):
        self.c = c
        self.w = w
        self.f = f
        self.win = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.store = set()

    def _admit(self, cand):
        if len(self.prob) + len(self.prot) < self.c - self.w:
            self.prob[cand] = 1
            return
        src = self.prob if self.prob else self.prot
        vic = next(iter(src))
        f = self.f
        if f.get(cand, 0) > f.get(vic, 0):
            del src[vic]
            self.store.discard(vic)
            self.prob[cand] = 1
        else:
            self.store.discard(cand)

    def resize(self, nw):
        if nw < self.w:
            self.w = nw
            while len(self.win) > nw:
                k, _ = self.win.popitem(last=False)
                self._admit(k)
        elif nw > self.w:
            self.w = nw
            while len(self.prob) + len(self.prot) > self.c - nw:
                src = self.prob if self.prob else self.prot
                k, _ = src.popitem(last=False)
                self.store.discard(k)

    def access(self, key):
        if key in self.win:
            self.win.move_to_end(key)
            return True
        if key in self.prob:
            del self.prob[key]
            self.prot[key] = 1
            pmax = int((self.c - self.w) * 0.3)
            while len(self.prot) > pmax:
                k, _ = self.prot.popitem(last=False)
                self.prob[k] = 1
            return True
        if key in self.prot:
            self.prot.move_to_end(key)
            return True
        self.store.add(key)
        self.win[key] = 1
        while len(self.win) > self.w:
            cand, _ = self.win.popitem(last=False)
            self._admit(cand)
        return False


class _Freq:
    def __init__(self, reset):
        self.d = {}
        self.n = 0
        self.reset = reset

    def add(self, k):
        d = self.d
        d[k] = d.get(k, 0) + 1
        self.n += 1
        if self.n >= self.reset:
            self.n //= 2
            nd = {k: v >> 1 for k, v in d.items() if v > 1}
            d.clear()
            d.update(nd)


class Cache:
    FRACS = (0.01, 0.05, 0.2, 0.9)
    RESETS = (4, 10, 30, 100)
    PERIOD = 1.0
    DECAY = 0.97

    def __init__(self, capacity):
        c = self.c = capacity
        self.freqs = [_Freq(m * c) for m in self.RESETS]
        ws = [max(1, min(c - 1, int(c * x))) for x in self.FRACS]
        self.cfg = [(w, fq) for fq in self.freqs for w in ws]
        self.shadows = [_TL(c, w, fq.d) for w, fq in self.cfg]
        self.score = [0.0] * len(self.cfg)
        self.cur = len(ws)
        self.real = _TL(c, self.cfg[self.cur][0], self.cfg[self.cur][1].d)
        self.store = self.real.store
        self.t = 0
        self.period = max(1, int(self.PERIOD * c))

    def access(self, key):
        for fq in self.freqs:
            fq.add(key)
        sc = self.score
        i = 0
        for s in self.shadows:
            if key in s.store:
                sc[i] += 1
            s.access(key)
            i += 1
        h = self.real.access(key)
        self.t += 1
        if self.t >= self.period:
            self.t = 0
            best = max(range(len(sc)), key=lambda j: sc[j])
            if sc[best] > sc[self.cur] * 1.03 + 1:
                self.cur = best
                w, fq = self.cfg[best]
                self.real.f = fq.d
                self.real.resize(w)
            d = self.DECAY
            for i in range(len(sc)):
                sc[i] *= d
        return h
