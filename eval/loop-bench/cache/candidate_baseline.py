from collections import OrderedDict


class Cache:
    """Least recently used."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.store = OrderedDict()

    def access(self, key):
        if key in self.store:
            self.store.move_to_end(key)
            return True
        if len(self.store) >= self.capacity:
            self.store.popitem(last=False)
        self.store[key] = True
        return False
