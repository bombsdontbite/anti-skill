from collections import OrderedDict


class Cache:
    """LRU behind a TinyLFU-style admission gate: a newcomer replaces the LRU victim only if seen more often."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.store = OrderedDict()
        self.freq = {}
        self.ops = 0
        self.age_at = 10 * capacity

    def access(self, key):
        fr = self.freq
        fr[key] = fr.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.age_at:
            self.ops = 0
            fr = {k: v >> 1 for k, v in fr.items() if v > 1}
            self.freq = fr
        st = self.store
        if key in st:
            st.move_to_end(key)
            return True
        if len(st) < self.capacity:
            st[key] = True
            return False
        victim = next(iter(st))
        if fr.get(key, 0) > fr.get(victim, 0):
            st.popitem(last=False)
            st[key] = True
        return False
