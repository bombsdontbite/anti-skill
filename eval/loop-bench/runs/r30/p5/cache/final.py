import random


class Cache:
    def __init__(self, capacity):
        self.c = capacity
        self.store = {}
        self.keys = []
        self.pos = {}
        self.freq = {}
        self.last = {}
        self.t = 0
        self.rng = random.Random(1)
        self.n = 0
        self.limit = 10 * capacity

    def access(self, key):
        self.t += 1
        f = self.freq
        self.n += 1
        if self.n >= self.limit:
            self.n = 0
            for k in list(f):
                v = f[k] >> 1
                if v:
                    f[k] = v
                else:
                    del f[k]
        f[key] = f.get(key, 0) + 1
        if key in self.store:
            self.last[key] = self.t
            return True
        if len(self.keys) >= self.c:
            keys = self.keys
            rnd = self.rng.random
            n = len(keys)
            best = None
            bk = None
            for _ in range(8):
                k = keys[int(rnd() * n)]
                b = (f.get(k, 0), self.last[k])
                if best is None or b < best:
                    best = b
                    bk = k
            if False:
                return False
            i = self.pos.pop(bk)
            lastk = keys.pop()
            if lastk != bk:
                keys[i] = lastk
                self.pos[lastk] = i
            del self.store[bk]
            del self.last[bk]
        self.pos[key] = len(self.keys)
        self.keys.append(key)
        self.store[key] = True
        self.last[key] = self.t
        return False
