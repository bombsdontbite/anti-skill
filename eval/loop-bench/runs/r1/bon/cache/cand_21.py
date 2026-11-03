import random


class Cache:
    """Redis-style approximate LFU: logarithmic counters that decay with idle time, sampled eviction."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.keys = []
        self.store = {}     # key -> index in keys
        self.ctr = {}
        self.ldt = {}
        self.last = {}
        self.t = 0
        self.decay = max(1, capacity)
        self.log_factor = 10
        self.init = 5
        self.samples = 10
        self.rng = random.Random(7)

    def _current(self, k):
        v = self.ctr[k]
        el = (self.t - self.ldt[k]) // self.decay
        return v - el if v > el else 0

    def _evict(self):
        keys = self.keys
        n = len(keys)
        rr = self.rng.random
        last = self.last
        best = None
        bs = None
        for _ in range(self.samples):
            k = keys[int(rr() * n)]
            s = (self._current(k), last[k])
            if bs is None or s < bs:
                bs = s
                best = k
        i = self.store.pop(best)
        tail = keys.pop()
        if tail != best:
            keys[i] = tail
            self.store[tail] = i
        del self.ctr[best]
        del self.ldt[best]
        del last[best]

    def access(self, key):
        self.t += 1
        t = self.t
        st = self.store
        if key in st:
            v = self._current(key)
            if v < 255:
                base = v - self.init if v > self.init else 0
                if self.rng.random() < 1.0 / (base * self.log_factor + 1):
                    v += 1
            self.ctr[key] = v
            self.ldt[key] = t
            self.last[key] = t
            return True
        if len(st) >= self.capacity:
            self._evict()
        st[key] = len(self.keys)
        self.keys.append(key)
        self.ctr[key] = self.init
        self.ldt[key] = t
        self.last[key] = t
        return False
