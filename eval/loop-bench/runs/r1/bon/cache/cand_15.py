import heapq
import math


class Cache:
    """LRFU: combined recency-frequency value with exponential decay, kept as a time-invariant log score."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.H = float(max(8, 2 * capacity))    # half-life in requests
        self.crf = {}
        self.last = {}
        self.store = {}     # key -> score
        self.heap = []
        self.t = 0
        self.next_prune = 4 * capacity

    def _prune(self, t):
        st = self.store
        horizon = 10.0 * self.H
        old = [k for k, lt in self.last.items() if k not in st and t - lt > horizon]
        for k in old:
            del self.last[k]
            del self.crf[k]
        self.next_prune = t + 4 * self.capacity

    def access(self, key):
        self.t += 1
        t = self.t
        H = self.H
        lt = self.last.get(key)
        if lt is None:
            c = 1.0
        else:
            c = 1.0 + self.crf[key] * 2.0 ** (-(t - lt) / H)
        self.crf[key] = c
        self.last[key] = t
        score = math.log2(c) + t / H
        st = self.store
        hit = key in st
        if not hit and len(st) >= self.capacity:
            h = self.heap
            last = self.last
            while True:
                _, ts, k = heapq.heappop(h)
                if k in st and last[k] == ts:
                    break
            del st[k]
        st[key] = score
        heapq.heappush(self.heap, (score, t, key))
        if len(self.heap) > 4 * self.capacity + 64:
            last = self.last
            self.heap = [(st[k], last[k], k) for k in st]
            heapq.heapify(self.heap)
        if t >= self.next_prune:
            self._prune(t)
        return hit
