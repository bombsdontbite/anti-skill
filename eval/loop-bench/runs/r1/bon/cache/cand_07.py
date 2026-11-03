from collections import OrderedDict


class Cache:
    """CAR: Clock with Adaptive Replacement — two clocks with reference bits, ARC-style ghosts."""

    def __init__(self, capacity):
        self.c = capacity
        self.p = 0.0
        self.t1 = OrderedDict()   # key -> ref bit; first = clock head
        self.t2 = OrderedDict()
        self.b1 = OrderedDict()
        self.b2 = OrderedDict()
        self.store = set()

    def _replace(self):
        t1 = self.t1
        t2 = self.t2
        while True:
            if t1 and (len(t1) >= max(1.0, self.p) or not t2):
                k, ref = t1.popitem(last=False)
                if ref:
                    t2[k] = 0
                else:
                    self.b1[k] = None
                    self.store.discard(k)
                    return
            else:
                k, ref = t2.popitem(last=False)
                if ref:
                    t2[k] = 0
                else:
                    self.b2[k] = None
                    self.store.discard(k)
                    return

    def access(self, key):
        if key in self.t1:
            self.t1[key] = 1
            return True
        if key in self.t2:
            self.t2[key] = 1
            return True
        c = self.c
        in_b1 = key in self.b1
        in_b2 = key in self.b2
        if len(self.t1) + len(self.t2) >= c:
            self._replace()
            if not in_b1 and not in_b2:
                if len(self.t1) + len(self.b1) >= c and self.b1:
                    self.b1.popitem(last=False)
                elif (len(self.t1) + len(self.t2) + len(self.b1) + len(self.b2) >= 2 * c
                      and self.b2):
                    self.b2.popitem(last=False)
        if in_b1:
            self.p = min(float(c), self.p + max(1.0, len(self.b2) / len(self.b1)))
            del self.b1[key]
            self.t2[key] = 0
        elif in_b2:
            self.p = max(0.0, self.p - max(1.0, len(self.b1) / len(self.b2)))
            del self.b2[key]
            self.t2[key] = 0
        else:
            self.t1[key] = 0
        self.store.add(key)
        return False
