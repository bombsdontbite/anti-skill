from collections import OrderedDict

FRACS = (0.01, 0.05, 0.15, 0.35, 0.6, 1.0)
RESETS = (4, 32)


class _Freq:
    """Exact counts halved every `period` requests."""

    def __init__(self, period):
        self.period = period
        self.ops = 0
        self.counts = {}

    def add(self, key):
        c = self.counts
        c[key] = c.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.period:
            self.ops = 0
            self.counts = {k: v >> 1 for k, v in c.items() if v > 1}


class _W:
    """W-TinyLFU body with a settable window size and frequency table."""

    def __init__(self, capacity, wmax, freq):
        self.capacity = capacity
        self.wmax = wmax
        self.freq = freq
        self.store = {}
        self.window = OrderedDict()
        self.probation = OrderedDict()
        self.protected = OrderedDict()
        self.score = 0.0

    def access(self, key):
        store = self.store
        if key in store:
            if key in self.window:
                self.window.move_to_end(key)
            elif key in self.protected:
                self.protected.move_to_end(key)
            else:
                del self.probation[key]
                self.protected[key] = True
                if len(self.protected) > (self.capacity - self.wmax) * 4 // 5:
                    k, _ = self.protected.popitem(last=False)
                    self.probation[k] = True
            return True
        counts = self.freq.counts
        store[key] = True
        self.window[key] = True
        while len(self.window) > self.wmax:
            cand, _ = self.window.popitem(last=False)
            self.probation[cand] = True
        while len(store) > self.capacity:
            if self.probation:
                victim = next(iter(self.probation))
                cand = next(reversed(self.probation))
                if cand != victim and counts.get(cand, 0) > counts.get(victim, 0):
                    out = victim
                else:
                    out = cand
                del self.probation[out]
            elif self.protected:
                out, _ = self.protected.popitem(last=False)
            else:
                out, _ = self.window.popitem(last=False)
            del store[out]
        pmax = (self.capacity - self.wmax) * 4 // 5
        while len(self.protected) > pmax:
            k, _ = self.protected.popitem(last=False)
            self.probation[k] = True
        return False


class Cache:
    """W-TinyLFU that copies window size and frequency aging from the best shadow cache."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.decay = 1.0 - 1.0 / (8 * capacity)
        self.freqs = [_Freq(r * capacity) for r in RESETS]
        sizes = sorted({min(capacity, max(1, round(f * capacity))) for f in FRACS})
        self.shadows = [_W(capacity, w, fr) for fr in self.freqs for w in sizes]
        self.main = _W(capacity, max(1, capacity // 100), self.freqs[0])
        self.store = self.main.store
        self.cur = None

    def access(self, key):
        for fr in self.freqs:
            fr.add(key)
        d = self.decay
        best = None
        for s in self.shadows:
            s.score = s.score * d + s.access(key)
            if best is None or s.score > best.score:
                best = s
        cur = self.cur
        if cur is None or best.score > cur.score * 1.02 + 1:
            self.cur = cur = best
        self.main.wmax = cur.wmax
        self.main.freq = cur.freq
        return self.main.access(key)
