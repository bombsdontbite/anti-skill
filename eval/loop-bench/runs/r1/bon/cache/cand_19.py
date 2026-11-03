import random


class Cache:
    """Belady approximation: predict each key's next use from its smoothed reuse gap, evict the furthest of a sample."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.keys = []
        self.store = {}     # key -> index in keys
        self.last = {}
        self.gap = {}
        self.t = 0
        self.rng = random.Random(99)
        self.k = 16
        self.horizon = 16 * capacity
        self.next_prune = 4 * capacity

    def _evict(self, t):
        keys = self.keys
        n = len(keys)
        rr = self.rng.random
        last = self.last
        gap = self.gap
        best = None
        bd = -1.0
        for _ in range(self.k):
            k = keys[int(rr() * n)]
            lt = last[k]
            g = gap.get(k)
            if g is None:
                d = 1e12 + (t - lt)
            else:
                nxt = lt + g
                d = nxt - t if nxt >= t else (t - lt) + g
            if d > bd:
                bd = d
                best = k
        i = self.store.pop(best)
        tail = keys.pop()
        if tail != best:
            keys[i] = tail
            self.store[tail] = i

    def _prune(self, t):
        st = self.store
        hz = self.horizon
        old = [k for k, lt in self.last.items() if k not in st and t - lt > hz]
        for k in old:
            del self.last[k]
            self.gap.pop(k, None)
        self.next_prune = t + 4 * self.capacity

    def access(self, key):
        self.t += 1
        t = self.t
        lt = self.last.get(key)
        if lt is not None:
            g = t - lt
            og = self.gap.get(key)
            self.gap[key] = g if og is None else 0.5 * og + 0.5 * g
        self.last[key] = t
        st = self.store
        if key in st:
            return True
        if len(st) >= self.capacity:
            self._evict(t)
        st[key] = len(self.keys)
        self.keys.append(key)
        if t >= self.next_prune:
            self._prune(t)
        return False
