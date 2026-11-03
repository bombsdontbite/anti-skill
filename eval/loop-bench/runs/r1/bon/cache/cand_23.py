import heapq
from collections import OrderedDict


class Cache:
    """Window-LFU: 10% LRU window in front of an aged-LFU main area; window leavers must out-count the LFU victim."""

    def __init__(self, capacity):
        c = capacity
        self.capacity = c
        self.wmax = max(1, c // 10)
        self.mmax = c - self.wmax
        self.win = OrderedDict()
        self.main = {}      # key -> tick of its valid heap entry
        self.heap = []
        self.freq = {}
        self.ops = 0
        self.age_at = 8 * c
        self.t = 0
        self.store = {}

    def _rebuild(self):
        fr = self.freq
        main = self.main
        self.heap = [(fr.get(k, 0), main[k], k) for k in main]
        heapq.heapify(self.heap)

    def _age(self):
        self.ops = 0
        self.freq = {k: v >> 1 for k, v in self.freq.items() if v > 1}
        self._rebuild()

    def _main_add(self, k, t):
        self.main[k] = t
        heapq.heappush(self.heap, (self.freq.get(k, 0), t, k))

    def _main_min(self):
        h = self.heap
        main = self.main
        while h:
            _, ts, k = h[0]
            if main.get(k) == ts:
                return k
            heapq.heappop(h)
        return None

    def access(self, key):
        self.t += 1
        t = self.t
        self.freq[key] = self.freq.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.age_at:
            self._age()
        st = self.store
        if key in st:
            if key in self.win:
                self.win.move_to_end(key)
            else:
                self._main_add(key, t)
                if len(self.heap) > 4 * self.capacity + 64:
                    self._rebuild()
            return True
        st[key] = True
        self.win[key] = None
        if len(self.win) > self.wmax:
            cand, _ = self.win.popitem(last=False)
            if len(self.main) < self.mmax:
                self._main_add(cand, t)
            else:
                vic = self._main_min()
                fr = self.freq
                if vic is not None and fr.get(cand, 0) > fr.get(vic, 0):
                    heapq.heappop(self.heap)
                    del self.main[vic]
                    del st[vic]
                    self._main_add(cand, t)
                else:
                    del st[cand]
        return False
