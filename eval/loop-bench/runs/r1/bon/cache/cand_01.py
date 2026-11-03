from collections import OrderedDict


class Cache:
    """ARC: adaptive split between recency (T1) and frequency (T2), steered by ghost hits."""

    def __init__(self, capacity):
        self.c = capacity
        self.p = 0.0
        self.t1 = OrderedDict()
        self.t2 = OrderedDict()
        self.b1 = OrderedDict()
        self.b2 = OrderedDict()
        self.store = {}

    def _replace(self, in_b2):
        t1 = self.t1
        if t1 and (len(t1) > self.p or (in_b2 and len(t1) >= self.p) or not self.t2):
            k, _ = t1.popitem(last=False)
            self.b1[k] = None
        else:
            k, _ = self.t2.popitem(last=False)
            self.b2[k] = None
        del self.store[k]

    def access(self, key):
        if key in self.store:
            if key in self.t1:
                del self.t1[key]
                self.t2[key] = None
            else:
                self.t2.move_to_end(key)
            return True
        c = self.c
        full = len(self.store) >= c
        if key in self.b1:
            lb1 = len(self.b1)
            lb2 = len(self.b2)
            self.p = min(float(c), self.p + max(1.0, lb2 / lb1))
            del self.b1[key]
            if full:
                self._replace(False)
            self.t2[key] = None
        elif key in self.b2:
            lb1 = len(self.b1)
            lb2 = len(self.b2)
            self.p = max(0.0, self.p - max(1.0, lb1 / lb2))
            del self.b2[key]
            if full:
                self._replace(True)
            self.t2[key] = None
        else:
            l1 = len(self.t1) + len(self.b1)
            if l1 >= c:
                if len(self.t1) < c and self.b1:
                    self.b1.popitem(last=False)
                    if full:
                        self._replace(False)
                else:
                    k, _ = self.t1.popitem(last=False)
                    del self.store[k]
            else:
                total = l1 + len(self.t2) + len(self.b2)
                if total >= c:
                    if total >= 2 * c and self.b2:
                        self.b2.popitem(last=False)
                    if full:
                        self._replace(False)
            self.t1[key] = None
        self.store[key] = True
        return False
