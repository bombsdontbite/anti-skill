from collections import OrderedDict


class Cache:
    """Window TinyLFU with exact aged counts and segmented main."""

    def __init__(self, capacity):
        self.c = capacity
        self.wmax = max(1, capacity // 10)
        self.mmax = capacity - self.wmax
        self.pmax = int(self.mmax * 0.8)
        self.win = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.freq = {}
        self.n = 0
        self.period = 3 * capacity
        self.store = set()

    def _age(self):
        f = self.freq
        for k in list(f):
            v = f[k] >> 1
            if v:
                f[k] = v
            else:
                del f[k]

    def access(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.n += 1
        if self.n >= self.period:
            self.n = 0
            self._age()
        if key in self.win:
            self.win.move_to_end(key)
            return True
        if key in self.prot:
            self.prot.move_to_end(key)
            return True
        if key in self.prob:
            del self.prob[key]
            self.prot[key] = True
            if len(self.prot) > self.pmax:
                k, _ = self.prot.popitem(last=False)
                self.prob[k] = True
            return True
        self.store.add(key)
        self.win[key] = True
        if len(self.win) > self.wmax:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mmax:
                self.prob[cand] = True
            else:
                vic = next(iter(self.prob)) if self.prob else next(iter(self.prot))
                if f.get(cand, 0) > f.get(vic, 0):
                    if self.prob:
                        self.prob.popitem(last=False)
                    else:
                        self.prot.popitem(last=False)
                    self.store.discard(vic)
                    self.prob[cand] = True
                else:
                    self.store.discard(cand)
        return False
