import random


class Cache:
    """Evict the sampled key whose next access is predicted furthest away."""

    def __init__(self, capacity, k=32, i0=10.0, a=0.5, seed=1, amin=0.1, beta=0.8, eta=0.05, gw=2.0, imin=1.0, imax=50.0, w=0.2):
        self.capacity = capacity
        self.store = {}
        self.keys = []
        self.last = {}
        self.ival = {}
        self.t = 0
        self.k = k
        self.i0 = i0 * capacity
        self.a = a
        self.amin = amin
        self.beta = beta
        self.cnt = {}
        self.eta = eta
        self.gw = gw * capacity
        self.imin = imin * capacity
        self.imax = imax * capacity
        self.ghost = {}
        self.w = w
        self.rng = random.Random(seed)

    def access(self, x):
        t = self.t = self.t + 1
        last, ival = self.last, self.ival
        lt = last.get(x)
        if lt is not None:
            d = t - lt
            iv = ival.get(x)
            if self.amin is None:
                a = self.a
            else:
                c = self.cnt[x] = self.cnt.get(x, 1) + 1
                a = max(1.0 / (c - 1), self.amin)
            ival[x] = d if iv is None else iv + a * (d - iv)
        last[x] = t
        store = self.store
        if x in store:
            return True
        keys = self.keys
        if self.eta:
            gh = self.ghost.pop(x, None)
            if gh is not None and t - gh[0] < self.gw:
                if gh[1]:
                    self.i0 = max(self.imin, self.i0 * (1 - self.eta))
                else:
                    self.i0 = min(self.imax, self.i0 * (1 + self.eta))
        if len(keys) >= self.capacity:
            rnd = self.rng.random
            n = len(keys)
            best = -1
            bi = 0
            i0 = self.i0
            beta = self.beta
            w = self.w
            cnt = self.cnt
            for _ in range(self.k):
                i = int(rnd() * n)
                y = keys[i]
                ly = last[y]
                iv = ival.get(y)
                if iv is None:
                    iv = i0
                elif w:
                    c = cnt[y] - 1
                    iv = (c * iv + w * i0) / (c + w)
                p = ly + iv - t
                o = (t - ly) * beta
                s = p if p > o else o
                if s > best:
                    best = s
                    bi = i
            y = keys[bi]
            if self.eta:
                self.ghost[y] = (t, y not in ival)
            z = keys.pop()
            if bi < len(keys):
                keys[bi] = z
                store[z] = bi
            del store[y]
        store[x] = len(keys)
        keys.append(x)
        return False
