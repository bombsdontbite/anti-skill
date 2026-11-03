from collections import OrderedDict


class Cache:
    """SLRU whose protected share adapts ARC-style: ghost hits say which segment was too small."""

    def __init__(self, capacity):
        c = capacity
        self.capacity = c
        self.target = c / 2.0
        self.delta = max(1.0, c / 64.0)
        self.prob = OrderedDict()   # key -> was it ever protected
        self.prot = OrderedDict()
        self.ghost = OrderedDict()  # key -> was it protected before eviction
        self.store = set()

    def _balance(self):
        prot = self.prot
        while prot and len(prot) > self.target:
            k, _ = prot.popitem(last=False)
            self.prob[k] = True

    def access(self, key):
        if key in self.prot:
            self.prot.move_to_end(key)
            return True
        if key in self.prob:
            del self.prob[key]
            self.prot[key] = None
            self._balance()
            return True
        c = self.capacity
        g = self.ghost.pop(key, None)
        if g is not None:
            if g:
                self.target = min(c - 1.0, self.target + self.delta)
            else:
                self.target = max(1.0, self.target - self.delta)
        if len(self.store) >= c:
            if self.prob:
                k, flag = self.prob.popitem(last=False)
            else:
                k, _ = self.prot.popitem(last=False)
                flag = True
            self.store.discard(k)
            self.ghost[k] = flag
            if len(self.ghost) > c:
                self.ghost.popitem(last=False)
        self.store.add(key)
        if g is not None:
            self.prot[key] = None
            self._balance()
        else:
            self.prob[key] = False
        return False
