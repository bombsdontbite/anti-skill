from collections import OrderedDict

WIN = 0.007
PROT = 0.8
AGE = 2


class Cache:
    def __init__(self, capacity):
        self.c = capacity
        self.w = max(1, int(capacity * WIN))
        self.mainc = capacity - self.w
        self.protc = int(self.mainc * PROT)
        self.win = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.freq = {}
        self.n = 0
        self.limit = AGE * capacity
        self.store = {}

    def _touch(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.n += 1
        if self.n >= self.limit:
            self.n = 0
            nf = {}
            for k, v in f.items():
                v >>= 1
                if v:
                    nf[k] = v
                    self.n += v
            self.freq = nf

    def access(self, key):
        self._touch(key)
        store = self.store
        if key in self.prot:
            self.prot.move_to_end(key)
            return True
        if key in self.prob:
            del self.prob[key]
            self.prot[key] = True
            if len(self.prot) > self.protc:
                k, _ = self.prot.popitem(last=False)
                self.prob[k] = True
            return True
        if key in self.win:
            self.win.move_to_end(key)
            return True
        self.win[key] = True
        store[key] = True
        if len(self.win) > self.w:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mainc:
                self.prob[cand] = True
            else:
                victim = next(iter(self.prob)) if self.prob else next(iter(self.prot))
                fc = self.freq.get(cand, 0)
                fv = self.freq.get(victim, 0)
                if fc > fv:
                    if self.prob:
                        self.prob.popitem(last=False)
                    else:
                        self.prot.popitem(last=False)
                    del store[victim]
                    self.prob[cand] = True
                else:
                    del store[cand]
        return False
