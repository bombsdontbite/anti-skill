from collections import OrderedDict


class Cache:
    """Full 2Q: FIFO A1in for first touches, ghost A1out, LRU Am for proven keys."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.kin = max(1, capacity // 4)
        self.kout = max(1, capacity // 2)
        self.a1in = OrderedDict()
        self.a1out = OrderedDict()
        self.am = OrderedDict()
        self.store = set()

    def _reclaim(self):
        if len(self.store) < self.capacity:
            return
        if len(self.a1in) > self.kin or not self.am:
            k, _ = self.a1in.popitem(last=False)
            self.a1out[k] = None
            if len(self.a1out) > self.kout:
                self.a1out.popitem(last=False)
        else:
            k, _ = self.am.popitem(last=False)
        self.store.discard(k)

    def access(self, key):
        if key in self.store:
            if key in self.am:
                self.am.move_to_end(key)
            return True
        self._reclaim()
        if key in self.a1out:
            del self.a1out[key]
            self.am[key] = None
        else:
            self.a1in[key] = None
        self.store.add(key)
        return False
