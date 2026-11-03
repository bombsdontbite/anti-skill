from collections import OrderedDict


class _Policy:
    """W-TinyLFU structures: LRU window + SLRU main with frequency-gated admission."""

    def __init__(self, capacity, wmax):
        self.capacity = capacity
        self.wmax = wmax
        self.store = {}
        self.window = OrderedDict()
        self.probation = OrderedDict()
        self.protected = OrderedDict()
        self.score = 0.0

    def access(self, key, est):
        store = self.store
        if key in store:
            if key in self.window:
                self.window.move_to_end(key)
            elif key in self.probation:
                del self.probation[key]
                self.protected[key] = True
                pmax = (self.capacity - self.wmax) * 4 // 5
                while len(self.protected) > pmax:
                    k, _ = self.protected.popitem(last=False)
                    self.probation[k] = True
            else:
                self.protected.move_to_end(key)
            return True
        window = self.window
        window[key] = True
        store[key] = True
        while len(window) > self.wmax:
            cand, _ = window.popitem(last=False)
            if len(store) <= self.capacity:
                self.probation[cand] = True
                continue
            src = self.probation or self.protected
            if not src:
                del store[cand]
                continue
            victim = next(iter(src))
            if est(cand) > est(victim):
                del src[victim]
                del store[victim]
                self.probation[cand] = True
            else:
                del store[cand]
        while len(store) > self.capacity:
            src = self.probation or self.protected or window
            k, _ = src.popitem(last=False)
            del store[k]
        return False


class _Sketch:
    """Saturating access counts with a doorkeeper, halved every `period` requests."""

    def __init__(self, period):
        self.period = period
        self.freq = {}
        self.door = set()
        self.samples = 0

    def add(self, key):
        if key not in self.door:
            self.door.add(key)
        else:
            c = self.freq.get(key, 0)
            if c < 7:
                self.freq[key] = c + 1
        self.samples += 1
        if self.samples >= self.period:
            self.samples = 0
            self.door = set()
            self.freq = {k: v >> 1 for k, v in self.freq.items() if v > 1}

    def est(self, key):
        return self.freq.get(key, 0) + (1 if key in self.door else 0)


class Cache:
    """W-TinyLFU whose window size and aging follow the best of several shadow simulations."""

    FRACTIONS = (0.01, 0.1, 0.25, 0.5, 0.8)
    PERIODS = (5,)

    def __init__(self, capacity):
        self.capacity = capacity
        self.sketches = [_Sketch(max(1, int(p * capacity))) for p in self.PERIODS]
        self.shadows = []
        for sk in self.sketches:
            for f in self.FRACTIONS:
                s = _Policy(capacity, max(1, min(capacity - 1, int(capacity * f))))
                s.sketch = sk
                self.shadows.append(s)
        self.best = self.shadows[0]
        self.real = _Policy(capacity, self.best.wmax)
        self.store = self.real.store
        self.decay = 1.0 - 1.0 / (5 * capacity)
        self.tick = 0
        self.period = max(1, capacity // 4)

    def access(self, key):
        for sk in self.sketches:
            sk.add(key)
        d = self.decay
        for s in self.shadows:
            s.score = s.score * d + s.access(key, s.sketch.est)
        self.tick += 1
        if self.tick >= self.period:
            self.tick = 0
            self.best = max(self.shadows, key=lambda s: s.score)
            self.real.wmax = self.best.wmax
        return self.real.access(key, self.best.sketch.est)
