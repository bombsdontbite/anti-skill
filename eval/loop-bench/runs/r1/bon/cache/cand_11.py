import heapq
import math
import random
from collections import OrderedDict


class Cache:
    """LeCaR: randomized mix of LRU and LFU experts, weights learned from regret on ghost hits."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.store = {}
        self.lru = OrderedDict()
        self.freq = {}
        self.stamp = {}
        self.heap = []
        self.t = 0
        self.hist_lru = OrderedDict()   # key -> (evict time, freq)
        self.hist_lfu = OrderedDict()
        self.w_lru = 0.5
        self.lr = 0.45
        self.disc = 0.005 ** (1.0 / max(1, capacity))
        self.rng = random.Random(4242)

    def _rebuild(self):
        self.heap = [(self.freq[k], self.stamp[k], k) for k in self.store]
        heapq.heapify(self.heap)

    def _lfu_victim(self):
        h = self.heap
        stamp = self.stamp
        while h:
            f, ts, k = h[0]
            if stamp.get(k) == ts:
                return k
            heapq.heappop(h)
        return next(iter(self.lru))

    def access(self, key):
        self.t += 1
        t = self.t
        st = self.store
        if key in st:
            self.lru.move_to_end(key)
            f = self.freq[key] + 1
            self.freq[key] = f
            self.stamp[key] = t
            heapq.heappush(self.heap, (f, t, key))
            if len(self.heap) > 4 * self.capacity + 64:
                self._rebuild()
            return True
        f = 1
        w = self.w_lru
        if key in self.hist_lru:
            et, f0 = self.hist_lru.pop(key)
            r = self.disc ** (t - et)
            wl = w * math.exp(-self.lr * r)
            w = wl / (wl + (1.0 - w))
            f = f0 + 1
        elif key in self.hist_lfu:
            et, f0 = self.hist_lfu.pop(key)
            r = self.disc ** (t - et)
            wf = (1.0 - w) * math.exp(-self.lr * r)
            w = w / (w + wf)
            f = f0 + 1
        if w < 0.01:
            w = 0.01
        elif w > 0.99:
            w = 0.99
        self.w_lru = w
        if len(st) >= self.capacity:
            if self.rng.random() < w:
                v = next(iter(self.lru))
                hist = self.hist_lru
            else:
                v = self._lfu_victim()
                hist = self.hist_lfu
            fv = self.freq.pop(v)
            del st[v]
            del self.lru[v]
            del self.stamp[v]
            hist[v] = (t, fv)
            if len(hist) > self.capacity:
                hist.popitem(last=False)
        st[key] = True
        self.lru[key] = None
        self.freq[key] = f
        self.stamp[key] = t
        heapq.heappush(self.heap, (f, t, key))
        return False
