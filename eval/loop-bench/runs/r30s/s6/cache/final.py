from collections import OrderedDict

WIN = 0.02
PROT = 0.6
TIE = 0   # admit if f(c) + TIE > f(v)
AGE = 6
CAP = 4


class Cache:
    def __init__(self, capacity):
        c = capacity
        self.capacity = c
        self.wmax = max(1, int(c * WIN))
        self.mmax = c - self.wmax
        self.pmax = max(1, int(self.mmax * PROT))
        self.win = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.freq = {}
        self.n = 0
        self.age = AGE * c
        self.store = set()

    def _touch(self, k):
        f = self.freq
        v = f.get(k, 0) + 1
        f[k] = v if v < CAP else CAP
        self.n += 1
        if self.n >= self.age:
            self.n = 0
            nf = {}
            for key, v in f.items():
                v >>= 1
                if v:
                    nf[key] = v
            self.freq = nf

    def access(self, key):
        self._touch(key)
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
        if key in self.win:
            self.win.move_to_end(key)
            return True
        self.win[key] = True
        self.store.add(key)
        if len(self.win) > self.wmax:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mmax:
                self.prob[cand] = True
            else:
                if self.prob:
                    vic = next(iter(self.prob))
                    if self.freq.get(cand, 0) + TIE > self.freq.get(vic, 0):
                        del self.prob[vic]
                        self.store.discard(vic)
                        self.prob[cand] = True
                    else:
                        self.store.discard(cand)
                else:
                    vic, _ = self.prot.popitem(last=False)
                    self.store.discard(vic)
                    self.prob[cand] = True
        return False
