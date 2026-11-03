from collections import OrderedDict, deque


class Cache:
    """S3-FIFO: small probation FIFO, main FIFO with 2-bit reinsertion, ghost of small evictions."""

    def __init__(self, capacity):
        c = capacity
        self.capacity = c
        self.smax = max(1, c // 10)
        self.gmax = max(1, c - self.smax)
        self.small = deque()
        self.main = deque()
        self.store = {}     # key -> frequency 0..3
        self.ghost = OrderedDict()

    def _evict(self):
        st = self.store
        small = self.small
        main = self.main
        while True:
            if small and (len(small) >= self.smax or not main):
                k = small.popleft()
                if st[k] > 0:
                    st[k] = 0
                    main.append(k)
                else:
                    del st[k]
                    self.ghost[k] = None
                    if len(self.ghost) > self.gmax:
                        self.ghost.popitem(last=False)
                    return
            else:
                k = main.popleft()
                f = st[k]
                if f > 0:
                    st[k] = f - 1
                    main.append(k)
                else:
                    del st[k]
                    return

    def access(self, key):
        st = self.store
        f = st.get(key)
        if f is not None:
            if f < 3:
                st[key] = f + 1
            return True
        if len(st) >= self.capacity:
            self._evict()
        if key in self.ghost:
            del self.ghost[key]
            self.main.append(key)
        else:
            self.small.append(key)
        st[key] = 0
        return False
