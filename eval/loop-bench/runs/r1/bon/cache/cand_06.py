import heapq


class Cache:
    """LFU with dynamic aging (LFUDA): priority = hits + L, L rises to each evicted priority."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.store = {}     # key -> current priority
        self.freq = {}
        self.stamp = {}
        self.heap = []
        self.L = 0.0
        self.t = 0

    def _rebuild(self):
        st = self.store
        self.heap = [(st[k], self.stamp[k], k) for k in st]
        heapq.heapify(self.heap)

    def access(self, key):
        self.t += 1
        t = self.t
        st = self.store
        if key in st:
            f = self.freq[key] + 1
            self.freq[key] = f
            pr = f + self.L
            st[key] = pr
            self.stamp[key] = t
            heapq.heappush(self.heap, (pr, t, key))
            if len(self.heap) > 4 * self.capacity + 64:
                self._rebuild()
            return True
        if len(st) >= self.capacity:
            h = self.heap
            while True:
                pr, ts, k = heapq.heappop(h)
                if k in st and self.stamp[k] == ts:
                    break
            self.L = pr
            del st[k]
            del self.freq[k]
            del self.stamp[k]
        pr = 1.0 + self.L
        st[key] = pr
        self.freq[key] = 1
        self.stamp[key] = t
        heapq.heappush(self.heap, (pr, t, key))
        return False
