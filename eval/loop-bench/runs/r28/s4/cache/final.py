import random


class Cache:
    """Approximate Belady: evict the sampled key predicted to return last."""

    def __init__(self, capacity, samples=24):
        self.cap = capacity
        self.samples = samples
        self.t = 0
        self.last = {}
        self.iv = {}
        self.keys = []
        self.pos = {}
        self.store = self.pos
        self.rng = random.Random(1)

    def _dist(self, k, now):
        last = self.last[k]
        iv = self.iv.get(k)
        if iv is None:
            return 1e9 + now - last
        d = last + iv - now
        return d if d >= 0 else now - last

    def access(self, key):
        now = self.t = self.t + 1
        last = self.last.get(key)
        if last is not None:
            gap = now - last
            old = self.iv.get(key)
            self.iv[key] = gap if old is None else (old + gap) / 2
        self.last[key] = now
        if key in self.pos:
            return True
        keys = self.keys
        if len(keys) >= self.cap:
            n = len(keys)
            rnd = self.rng.randrange
            best, bd = -1, -1.0
            for _ in range(self.samples):
                i = rnd(n)
                d = self._dist(keys[i], now)
                if d > bd:
                    best, bd = i, d
            k = keys[best]
            tail = keys.pop()
            if best < len(keys):
                keys[best] = tail
                self.pos[tail] = best
            del self.pos[k]
        self.pos[key] = len(keys)
        keys.append(key)
        return False
