import heapq
from collections import OrderedDict


class Cache:
    """LRU/LFU switch: miniature sampled shadow caches of each policy decide which one evicts for real."""

    def __init__(self, capacity):
        c = capacity
        self.capacity = c
        self.store = OrderedDict()  # recency order of the real cache
        self.freq = {}
        self.ops = 0
        self.age_at = 10 * c
        self.heap = []
        self.stamp = {}
        self.t = 0
        self.scap = max(4, c // 16)
        self.s_lru = OrderedDict()
        self.s_lfu = {}     # key -> last access time
        self.sc_lru = 0.0
        self.sc_lfu = 0.0
        self.decay = 0.995

    def _rebuild(self):
        fr = self.freq
        stamp = self.stamp
        self.heap = [(fr.get(k, 0), stamp[k], k) for k in self.store]
        heapq.heapify(self.heap)

    def _age(self):
        self.ops = 0
        self.freq = {k: v >> 1 for k, v in self.freq.items() if v > 1}
        self._rebuild()

    def _shadow(self, key, t):
        fr = self.freq
        sl = self.s_lru
        lh = key in sl
        if lh:
            sl.move_to_end(key)
        else:
            if len(sl) >= self.scap:
                sl.popitem(last=False)
            sl[key] = None
        sf = self.s_lfu
        fh = key in sf
        if not fh and len(sf) >= self.scap:
            victim = min(sf, key=lambda k: (fr.get(k, 0), sf[k]))
            del sf[victim]
        sf[key] = t
        d = self.decay
        self.sc_lru = self.sc_lru * d + (1.0 if lh else 0.0)
        self.sc_lfu = self.sc_lfu * d + (1.0 if fh else 0.0)

    def _lfu_victim(self):
        h = self.heap
        stamp = self.stamp
        while h:
            _, ts, k = h[0]
            if stamp.get(k) == ts:
                return k
            heapq.heappop(h)
        return next(iter(self.store))

    def access(self, key):
        self.t += 1
        t = self.t
        self.freq[key] = self.freq.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.age_at:
            self._age()
        if ((key * 0x9E3779B1) & 0xFFFFFFFF) >> 28 == 0:
            self._shadow(key, t)
        st = self.store
        fr = self.freq
        if key in st:
            st.move_to_end(key)
            self.stamp[key] = t
            heapq.heappush(self.heap, (fr.get(key, 0), t, key))
            if len(self.heap) > 4 * self.capacity + 64:
                self._rebuild()
            return True
        if len(st) >= self.capacity:
            if self.sc_lfu > self.sc_lru:
                victim = self._lfu_victim()
            else:
                victim = next(iter(st))
            del st[victim]
            del self.stamp[victim]
        st[key] = True
        self.stamp[key] = t
        heapq.heappush(self.heap, (fr.get(key, 0), t, key))
        return False
