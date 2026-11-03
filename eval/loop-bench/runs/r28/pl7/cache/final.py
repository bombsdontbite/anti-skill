from collections import OrderedDict


class Freq:
    def __init__(self, sample):
        self.f = {}
        self.ops = 0
        self.sample = sample

    def bump(self, key):
        f = self.f
        f[key] = f.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.sample:
            self.ops = 0
            self.f = {k: v >> 1 for k, v in f.items() if v > 1}


class TinyLFU:
    """LRU window in front of a frequency-gated SLRU main."""

    def __init__(self, capacity, wfrac, freq):
        self.capacity = capacity
        self.freq = freq
        self.store = set()
        self.window = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.wmax = max(1, int(capacity * wfrac))
        self.pmax = int(0.8 * (capacity - self.wmax))

    def access(self, key):
        if key in self.store:
            if key in self.window:
                self.window.move_to_end(key)
            elif key in self.prot:
                self.prot.move_to_end(key)
            else:
                del self.prob[key]
                self.prot[key] = True
                if len(self.prot) > self.pmax:
                    k, _ = self.prot.popitem(last=False)
                    self.prob[k] = True
            return True
        store, win, prob = self.store, self.window, self.prob
        store.add(key)
        win[key] = True
        if len(win) > self.wmax:
            c, _ = win.popitem(last=False)
            prob[c] = True
            if len(store) > self.capacity:
                vic = next(iter(prob))
                f = self.freq.f
                if vic != c and f.get(c, 0) <= f.get(vic, 0):
                    vic = c
                del prob[vic]
                store.discard(vic)
        return False


class LRU:
    def __init__(self, capacity):
        self.capacity = capacity
        self.store = OrderedDict()

    def access(self, key):
        if key in self.store:
            self.store.move_to_end(key)
            return True
        if len(self.store) >= self.capacity:
            self.store.popitem(last=False)
        self.store[key] = True
        return False


class Cache:
    """Follows whichever shadow policy has hit most recently."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.freqs = [Freq(5 * capacity), Freq(20 * capacity), Freq(100 * capacity)]
        fast, slow, vslow = self.freqs
        self.experts = [
            TinyLFU(capacity, 0.01, fast),
            TinyLFU(capacity, 0.2, fast),
            TinyLFU(capacity, 0.01, slow),
            LRU(capacity),
            TinyLFU(capacity, 0.01, vslow),
        ]
        self.scores = [0.0] * len(self.experts)
        self.leader = 0
        self.n = 0
        self.half = max(100, 2 * capacity)
        self.store = OrderedDict()

    def access(self, key):
        for fr in self.freqs:
            fr.bump(key)
        sc = self.scores
        for i, e in enumerate(self.experts):
            if e.access(key):
                sc[i] += 1
        self.n += 1
        if self.n >= self.half:
            self.n = 0
            for i in range(len(sc)):
                sc[i] *= 0.5
            best = self.leader
            for i in range(len(sc)):
                if sc[i] > sc[best] * 1.05 + 2:
                    best = i
            self.leader = best
        store = self.store
        if key in store:
            store.move_to_end(key)
            return True
        lead = self.experts[self.leader].store
        if key not in lead:
            return False
        if len(store) >= self.capacity:
            vic = None
            for k in store:
                if k not in lead:
                    vic = k
                    break
            if vic is None:
                vic = next(iter(store))
            del store[vic]
        store[key] = True
        return False
