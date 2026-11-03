from collections import OrderedDict

FRACS = (0.01, 0.05, 0.2, 0.5, 0.9)
PROT = 0.8
RESET = 10


class WTinyLFU:
    def __init__(self, capacity, wcap, freq):
        self.capacity = capacity
        self.store = {}
        self.window = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.freq = freq
        self.set_window(wcap)

    def set_window(self, wcap):
        self.wcap = wcap
        self.mcap = self.capacity - wcap
        self.pcap = int(self.mcap * PROT)
        while len(self.window) > wcap:
            k, _ = self.window.popitem(last=False)
            self.prob[k] = True
        while len(self.prot) > self.pcap:
            k, _ = self.prot.popitem(last=False)
            self.prob[k] = True
        while len(self.prob) + len(self.prot) > self.mcap:
            od = self.prob if self.prob else self.prot
            k, _ = od.popitem(last=False)
            del self.store[k]

    def access(self, key):
        if key in self.store:
            if key in self.window:
                self.window.move_to_end(key)
            elif key in self.prob:
                del self.prob[key]
                self.prot[key] = True
                if len(self.prot) > self.pcap:
                    k, _ = self.prot.popitem(last=False)
                    self.prob[k] = True
            else:
                self.prot.move_to_end(key)
            return True
        self.store[key] = True
        self.window[key] = True
        if len(self.window) > self.wcap:
            cand, _ = self.window.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = True
            else:
                victim_od = self.prob if self.prob else self.prot
                victim = next(iter(victim_od))
                f = self.freq.counts
                if f.get(cand, 0) > f.get(victim, 0):
                    del victim_od[victim]
                    del self.store[victim]
                    self.prob[cand] = True
                else:
                    del self.store[cand]
        return False


class Freq:
    def __init__(self, reset_at):
        self.counts = {}
        self.ops = 0
        self.reset_at = reset_at

    def add(self, key):
        c = self.counts
        c[key] = c.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.reset_at:
            self.ops //= 2
            self.counts = {k: v >> 1 for k, v in c.items() if v > 1}


class Cache:
    """W-TinyLFU whose window size follows the best of several shadow caches."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.freq = Freq(RESET * capacity)
        ws = [min(capacity - 1, max(1, int(capacity * f))) for f in FRACS]
        self.shadows = [WTinyLFU(capacity, w, self.freq) for w in ws]
        self.scores = [0.0] * len(ws)
        self.real = WTinyLFU(capacity, ws[0], self.freq)
        self.store = self.real.store
        self.n = 0
        self.period = capacity

    def access(self, key):
        self.freq.add(key)
        hit = self.real.access(key)
        sc = self.scores
        for i, s in enumerate(self.shadows):
            if s.access(key):
                sc[i] += 1
        self.n += 1
        if self.n >= self.period:
            self.n = 0
            best = sc.index(max(sc))
            w = self.shadows[best].wcap
            if w != self.real.wcap:
                self.real.set_window(w)
            self.scores = [x * 0.8 for x in sc]
        return hit
