import heapq


class Cache:
    """LRU-2: evict the key whose second-most-recent access is oldest; one-touch keys go first."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.store = set()
        self.t = 0
        self.last = {}
        self.prev = {}
        self.heap = []
        self.hist_limit = 4 * capacity + 16

    def _compact(self):
        if len(self.heap) > 3 * self.capacity + 64:
            prev = self.prev
            last = self.last
            self.heap = [(prev.get(k, -1), last[k], k) for k in self.store]
            heapq.heapify(self.heap)

    def _evict(self):
        h = self.heap
        st = self.store
        last = self.last
        while True:
            _, ts, k = heapq.heappop(h)
            if k in st and last[k] == ts:
                st.discard(k)
                return

    def _prune(self):
        st = self.store
        last = self.last
        nonres = [(lt, k) for k, lt in last.items() if k not in st]
        nonres.sort(reverse=True)
        newlast = {k: last[k] for k in st}
        for lt, k in nonres[: self.hist_limit // 2]:
            newlast[k] = lt
        prev = self.prev
        self.prev = {k: prev[k] for k in newlast if k in prev}
        self.last = newlast

    def access(self, key):
        self.t += 1
        t = self.t
        last = self.last
        lt = last.get(key)
        if lt is not None:
            self.prev[key] = lt
        last[key] = t
        if key in self.store:
            heapq.heappush(self.heap, (self.prev[key], t, key))
            self._compact()
            return True
        if len(self.store) >= self.capacity:
            self._evict()
        self.store.add(key)
        heapq.heappush(self.heap, (self.prev.get(key, -1), t, key))
        if len(last) - len(self.store) > self.hist_limit:
            self._prune()
        self._compact()
        return False
