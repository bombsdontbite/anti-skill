import random
from collections import OrderedDict


class Cache:
    """Dynamic insertion (DIP): LRU vs bimodal LRU-position insertion, chosen by set dueling on key hashes."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.store = OrderedDict()
        self.psel = 512
        self.rng = random.Random(31337)

    def access(self, key):
        st = self.store
        if key in st:
            st.move_to_end(key)
            return True
        g = ((key * 2654435761) & 0xFFFFFFFF) >> 27
        if g == 0:
            if self.psel < 1023:
                self.psel += 1
            bip = False
        elif g == 1:
            if self.psel > 0:
                self.psel -= 1
            bip = True
        else:
            bip = self.psel > 512
        if len(st) >= self.capacity:
            st.popitem(last=False)
        st[key] = True
        if bip and self.rng.random() >= 1.0 / 32:
            st.move_to_end(key, last=False)
        return False
