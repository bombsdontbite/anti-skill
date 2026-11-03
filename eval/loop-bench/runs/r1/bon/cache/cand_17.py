class Cache:
    """GCLOCK: fixed slot ring, saturating hit counters, the hand decrements until it finds a zero."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.slots = []
        self.cnt = []
        self.store = {}     # key -> slot index
        self.hand = 0
        self.max_count = 3

    def access(self, key):
        st = self.store
        i = st.get(key)
        if i is not None:
            if self.cnt[i] < self.max_count:
                self.cnt[i] += 1
            return True
        slots = self.slots
        cnt = self.cnt
        if len(slots) < self.capacity:
            st[key] = len(slots)
            slots.append(key)
            cnt.append(0)
            return False
        n = len(slots)
        h = self.hand
        while cnt[h] > 0:
            cnt[h] -= 1
            h += 1
            if h == n:
                h = 0
        del st[slots[h]]
        slots[h] = key
        cnt[h] = 0
        st[key] = h
        h += 1
        if h == n:
            h = 0
        self.hand = h
        return False
