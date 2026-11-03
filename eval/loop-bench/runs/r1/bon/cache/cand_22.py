from collections import OrderedDict


class Cache:
    """Four-level segmented LRU: each hit climbs one level, overflow cascades down, evict from the lowest."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.levels = 4
        self.segs = [OrderedDict() for _ in range(self.levels)]
        q = max(1, capacity // 4)
        self.smax = [capacity] + [q] * (self.levels - 1)
        self.store = {}     # key -> level

    def access(self, key):
        st = self.store
        segs = self.segs
        lv = st.get(key)
        if lv is not None:
            top = self.levels - 1
            if lv == top:
                segs[top].move_to_end(key)
            else:
                del segs[lv][key]
                nl = lv + 1
                segs[nl][key] = None
                st[key] = nl
                j = nl
                while j > 0 and len(segs[j]) > self.smax[j]:
                    k, _ = segs[j].popitem(last=False)
                    segs[j - 1][k] = None
                    st[k] = j - 1
                    j -= 1
            return True
        if len(st) >= self.capacity:
            for s in segs:
                if s:
                    k, _ = s.popitem(last=False)
                    del st[k]
                    break
        segs[0][key] = None
        st[key] = 0
        return False
