class Cache:
    """SIEVE: FIFO order, visited bit, a hand that sweeps oldest-to-newest and keeps visited keys in place."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.store = {}     # key -> visited
        self.newer = {}
        self.older = {}
        self.head = None    # newest
        self.tail = None    # oldest
        self.hand = None

    def _evict(self):
        st = self.store
        newer = self.newer
        o = self.hand
        if o is None:
            o = self.tail
        while st[o]:
            st[o] = False
            o = newer[o]
            if o is None:
                o = self.tail
        self.hand = newer[o]
        a = self.older.pop(o)
        b = newer.pop(o)
        if a is not None:
            newer[a] = b
        else:
            self.tail = b
        if b is not None:
            self.older[b] = a
        else:
            self.head = a
        del st[o]

    def access(self, key):
        st = self.store
        if key in st:
            st[key] = True
            return True
        if len(st) >= self.capacity:
            self._evict()
        st[key] = False
        h = self.head
        self.older[key] = h
        self.newer[key] = None
        if h is not None:
            self.newer[h] = key
        else:
            self.tail = key
        self.head = key
        return False
