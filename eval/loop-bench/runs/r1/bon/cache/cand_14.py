from collections import OrderedDict


class Cache:
    """Multi-Queue (MQ): LRU queues by log2(frequency), idle keys demote, ghost keeps frequency."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.m = 8
        self.qs = [OrderedDict() for _ in range(self.m)]
        self.store = {}     # key -> queue level
        self.freq = {}
        self.expire = {}
        self.qout = OrderedDict()
        self.qout_max = 4 * capacity
        self.life = 4 * capacity
        self.t = 0

    def _level(self, f):
        i = f.bit_length() - 1
        return i if i < self.m else self.m - 1

    def _evict(self):
        for q in self.qs:
            if q:
                k, _ = q.popitem(last=False)
                del self.store[k]
                del self.expire[k]
                self.qout[k] = self.freq.pop(k)
                if len(self.qout) > self.qout_max:
                    self.qout.popitem(last=False)
                return

    def _adjust(self, t):
        qs = self.qs
        for i in range(1, self.m):
            q = qs[i]
            if q:
                k = next(iter(q))
                if self.expire[k] < t:
                    del q[k]
                    qs[i - 1][k] = None
                    self.store[k] = i - 1
                    self.expire[k] = t + self.life

    def access(self, key):
        self.t += 1
        t = self.t
        st = self.store
        if key in st:
            del self.qs[st[key]][key]
            f = self.freq[key] + 1
            hit = True
        else:
            if len(st) >= self.capacity:
                self._evict()
            f = self.qout.pop(key, 0) + 1
            hit = False
        self.freq[key] = f
        lv = self._level(f)
        self.qs[lv][key] = None
        st[key] = lv
        self.expire[key] = t + self.life
        self._adjust(t)
        return hit
