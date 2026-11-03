from collections import OrderedDict


class Cache:
    """Window LRU + main LRU with frequency admission; window size hill-climbed."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.store = {}
        self.wmax = max(1, int(capacity * 0.8))
        self.wsize = max(1, capacity // 20)
        self.step = max(1, capacity // 20)
        self.dir = 1
        self.period = 8 * capacity
        self.hits = 0
        self.t = 0
        self.prev = -1.0
        self.win = OrderedDict()
        self.main = OrderedDict()
        self.freq = {}
        self.n = 0
        self.limit = 6 * capacity

    def _adapt(self):
        rate = self.hits / self.t
        if self.prev >= 0 and rate < self.prev:
            self.dir = -self.dir
        self.prev = rate
        self.hits = 0
        self.t = 0
        self.wsize = min(self.wmax, max(1, self.wsize + self.dir * self.step))

    def access(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.n += 1
        if self.n >= self.limit:
            self.n = 0
            for k in list(f):
                v = f[k] >> 1
                if v:
                    f[k] = v
                else:
                    del f[k]
        self.t += 1
        if self.t >= self.period:
            self._adapt()
        main = self.main
        win = self.win
        if key in main:
            main.move_to_end(key)
            self.hits += 1
            return True
        if key in win:
            win.move_to_end(key)
            self.hits += 1
            return True
        win[key] = True
        self.store[key] = True
        cap = self.capacity
        while len(win) > self.wsize:
            cand, _ = win.popitem(last=False)
            if len(main) + len(win) < cap:
                main[cand] = True
            elif not main:
                del self.store[cand]
            else:
                victim = next(iter(main))
                if f.get(cand, 0) > f.get(victim, 0):
                    del main[victim]
                    del self.store[victim]
                    main[cand] = True
                else:
                    del self.store[cand]
        if len(main) + len(win) > cap:
            victim, _ = main.popitem(last=False)
            del self.store[victim]
        return False
