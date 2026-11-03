from collections import OrderedDict


class _WTinyLFU:
    def __init__(self, capacity, wcap, freq):
        self.capacity = capacity
        self.store = {}
        self.freq = freq
        self.window = OrderedDict()
        self.probation = OrderedDict()
        self.protected = OrderedDict()
        self.resize(wcap)

    def resize(self, wcap):
        self.wcap = wcap
        self.mcap = self.capacity - wcap
        self.pcap = int(self.mcap * 0.6)
        while len(self.window) > wcap:
            k, _ = self.window.popitem(last=False)
            self.probation[k] = True
        while len(self.protected) > self.pcap:
            k, _ = self.protected.popitem(last=False)
            self.probation[k] = True
        while len(self.probation) + len(self.protected) > self.mcap:
            if self.probation:
                k, _ = self.probation.popitem(last=False)
            else:
                k, _ = self.protected.popitem(last=False)
            del self.store[k]

    def access(self, key):
        if key in self.store:
            if key in self.window:
                self.window.move_to_end(key)
            elif key in self.protected:
                self.protected.move_to_end(key)
            else:
                del self.probation[key]
                self.protected[key] = True
                if len(self.protected) > self.pcap:
                    k, _ = self.protected.popitem(last=False)
                    self.probation[k] = True
            return True
        self.store[key] = True
        self.window[key] = True
        if len(self.window) > self.wcap:
            cand, _ = self.window.popitem(last=False)
            if len(self.probation) + len(self.protected) < self.mcap:
                self.probation[cand] = True
            else:
                victim = next(iter(self.probation)) if self.probation else next(iter(self.protected))
                f = self.freq.f
                if f.get(cand, 0) > f.get(victim, 0):
                    if victim in self.probation:
                        del self.probation[victim]
                    else:
                        del self.protected[victim]
                    del self.store[victim]
                    self.probation[cand] = True
                else:
                    del self.store[cand]
        return False


class _Freq:
    def __init__(self, reset):
        self.f = {}
        self.ops = 0
        self.reset = reset

    def add(self, key):
        f = self.f
        f[key] = f.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.f = {k: v >> 1 for k, v in f.items() if v > 1}


class Cache:
    """W-TinyLFU whose window size and frequency aging follow the best of several shadow copies."""

    FRACTIONS = (0.01, 0.1, 0.4, 0.9)
    RESETS = (3, 8, 20, 60)
    DECAY = 0.999
    EVERY = 0.25
    MARGIN = 1.03

    def __init__(self, capacity):
        self.freqs = [_Freq(r * capacity) for r in self.RESETS]
        sizes = [min(capacity - 1, max(1, int(capacity * x))) for x in self.FRACTIONS]
        self.configs = [(w, f) for f in self.freqs for w in sizes]
        self.main = _WTinyLFU(capacity, sizes[0], self.freqs[1])
        self.cur = len(sizes)
        self.store = self.main.store
        self.shadows = [_WTinyLFU(capacity, w, f) for w, f in self.configs]
        self.scores = [0.0] * len(self.configs)
        self.every = max(1, int(capacity * self.EVERY))
        self.n = 0

    def access(self, key):
        for f in self.freqs:
            f.add(key)
        hit = self.main.access(key)
        d = self.DECAY
        sc = self.scores
        for i, s in enumerate(self.shadows):
            sc[i] = sc[i] * d + s.access(key)
        self.n += 1
        if self.n >= self.every:
            self.n = 0
            best = max(range(len(sc)), key=lambda i: sc[i])
            if sc[best] <= sc[self.cur] * self.MARGIN:
                return hit
            self.cur = best
            w, f = self.configs[best]
            self.main.freq = f
            if w != self.main.wcap:
                self.main.resize(w)
        return hit
