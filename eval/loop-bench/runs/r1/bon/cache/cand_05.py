from collections import OrderedDict


class Cache:
    """Segmented LRU: 20% probation for new keys, 80% protected for keys hit twice."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.pmax = max(1, int(capacity * 0.8))
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.store = set()

    def access(self, key):
        if key in self.prot:
            self.prot.move_to_end(key)
            return True
        if key in self.prob:
            del self.prob[key]
            self.prot[key] = None
            if len(self.prot) > self.pmax:
                k, _ = self.prot.popitem(last=False)
                self.prob[k] = None
            return True
        if len(self.store) >= self.capacity:
            src = self.prob if self.prob else self.prot
            k, _ = src.popitem(last=False)
            self.store.discard(k)
        self.prob[key] = None
        self.store.add(key)
        return False
