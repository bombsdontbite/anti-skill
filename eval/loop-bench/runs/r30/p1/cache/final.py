from collections import OrderedDict

WIN = 0.1
AGE = 6
DECAY = 0.999


class Base:
    def __init__(self, capacity):
        self.c = capacity
        self.wmax = max(1, int(capacity * WIN))
        self.win = OrderedDict()
        self.main = OrderedDict()
        self.f = {}
        self.n = 0
        self.limit = AGE * capacity
        self.strict = True
        self.store = set()

    def access(self, key):
        f = self.f
        f[key] = f.get(key, 0) + 1
        self.n += 1
        if self.n >= self.limit:
            self.n = 0
            self.f = f = {k: v >> 1 for k, v in f.items() if v > 1}
        if key in self.main:
            self.main.move_to_end(key)
            return True
        if key in self.win:
            self.win.move_to_end(key)
            return True
        self.win[key] = True
        self.store.add(key)
        if len(self.win) > self.wmax:
            cand, _ = self.win.popitem(last=False)
            if len(self.main) < self.c - self.wmax:
                self.main[cand] = True
            else:
                vic = next(iter(self.main))
                if not self.strict or f.get(cand, 0) > f.get(vic, 0):
                    del self.main[vic]
                    self.store.discard(vic)
                    self.main[cand] = True
                else:
                    self.store.discard(cand)
        return False


class Cache(Base):
    def __init__(self, capacity):
        Base.__init__(self, capacity)
        self.a = Base(capacity)
        self.b = Base(capacity)
        self.b.strict = False
        self.ha = 0.0
        self.hb = 0.0

    def access(self, key):
        self.ha = self.ha * DECAY + self.a.access(key)
        self.hb = self.hb * DECAY + self.b.access(key)
        self.strict = self.ha >= self.hb
        return Base.access(self, key)
