from collections import OrderedDict


class Cache:
    """Adaptive W-TinyLFU: window/main split tuned by hill climbing on the hit rate of each period."""

    def __init__(self, capacity):
        c = capacity
        self.capacity = c
        self.wmax = max(1, c // 20)
        self.mmax = c - self.wmax
        self.pmax = int(self.mmax * 0.8)
        self.win = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.store = {}
        self.freq = {}
        self.ops = 0
        self.age_at = 10 * c
        self.period = max(256, 4 * c)
        self.p_req = 0
        self.p_hit = 0
        self.prev_rate = -1.0
        self.base_step = max(1, c // 16)
        self.step = self.base_step
        self.direction = 1

    def _count(self, key):
        fr = self.freq
        fr[key] = fr.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.age_at:
            self.ops = 0
            self.freq = {k: v >> 1 for k, v in fr.items() if v > 1}

    def _resize(self, nw):
        self.wmax = nw
        self.mmax = self.capacity - nw
        self.pmax = int(self.mmax * 0.8)
        win = self.win
        prob = self.prob
        prot = self.prot
        while len(win) > self.wmax:
            k, _ = win.popitem(last=False)
            prob[k] = None
        while len(prob) + len(prot) > self.mmax:
            if prob:
                k, _ = prob.popitem(last=False)
            else:
                k, _ = prot.popitem(last=False)
            win[k] = None
            win.move_to_end(k, last=False)
        while len(prot) > self.pmax:
            k, _ = prot.popitem(last=False)
            prob[k] = None

    def _climb(self):
        rate = self.p_hit / self.p_req
        self.p_hit = 0
        self.p_req = 0
        if self.prev_rate >= 0:
            delta = rate - self.prev_rate
            if delta < 0:
                self.direction = -self.direction
            if abs(delta) > 0.05:
                self.step = self.base_step
            else:
                self.step = max(1, int(self.step * 0.9))
        self.prev_rate = rate
        c = self.capacity
        hi = c - 1 if c > 1 else 1
        nw = self.wmax + self.direction * self.step
        if nw < 1:
            nw = 1
        if nw > hi:
            nw = hi
        if nw != self.wmax:
            self._resize(nw)

    def _lookup(self, key):
        st = self.store
        if key in st:
            if key in self.win:
                self.win.move_to_end(key)
            elif key in self.prot:
                self.prot.move_to_end(key)
            else:
                del self.prob[key]
                self.prot[key] = None
                if len(self.prot) > self.pmax:
                    k, _ = self.prot.popitem(last=False)
                    self.prob[k] = None
            return True
        st[key] = True
        self.win[key] = None
        if len(self.win) > self.wmax:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mmax:
                self.prob[cand] = None
            else:
                src = self.prob if self.prob else self.prot
                if not src:
                    del st[cand]
                else:
                    vic = next(iter(src))
                    fr = self.freq
                    if fr.get(cand, 0) > fr.get(vic, 0):
                        del src[vic]
                        del st[vic]
                        self.prob[cand] = None
                    else:
                        del st[cand]
        return False

    def access(self, key):
        self._count(key)
        hit = self._lookup(key)
        self.p_req += 1
        if hit:
            self.p_hit += 1
        if self.p_req >= self.period:
            self._climb()
        return hit
