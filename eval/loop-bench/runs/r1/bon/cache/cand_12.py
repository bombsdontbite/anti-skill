import random


class Cache:
    """Hyperbolic caching: evict the sampled key with the lowest hits-per-time-in-cache."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.keys = []
        self.store = {}     # key -> index in keys
        self.count = {}
        self.born = {}
        self.t = 0
        self.rng = random.Random(2024)
        self.k = 16

    def _evict(self):
        keys = self.keys
        n = len(keys)
        t = self.t
        rr = self.rng.random
        cnt = self.count
        born = self.born
        best = None
        bs = 0.0
        for _ in range(self.k):
            k = keys[int(rr() * n)]
            s = cnt[k] / (t - born[k] + 1.0)
            if best is None or s < bs:
                bs = s
                best = k
        i = self.store.pop(best)
        last = keys.pop()
        if last != best:
            keys[i] = last
            self.store[last] = i
        del cnt[best]
        del born[best]

    def access(self, key):
        self.t += 1
        st = self.store
        if key in st:
            self.count[key] += 1
            return True
        if len(st) >= self.capacity:
            self._evict()
        st[key] = len(self.keys)
        self.keys.append(key)
        self.count[key] = 1
        self.born[key] = self.t
        return False
