from collections import OrderedDict

M64 = 0xFFFFFFFFFFFFFFFF


class Cache:
    """W-TinyLFU: 1% LRU window, SLRU main, count-min sketch admission with periodic halving."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.wmax = max(1, capacity // 100)
        self.mmax = capacity - self.wmax
        self.pmax = int(self.mmax * 0.8)
        width = 64
        while width < 4 * capacity and width < (1 << 16):
            width <<= 1
        self.mask = width - 1
        self.rows = [[0] * width for _ in range(4)]
        self.samples = 0
        self.reset_at = 10 * capacity
        self.win = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.store = {}

    def _hashes(self, key):
        h = (key * 0x9E3779B97F4A7C15 + 0x7F4A7C159E3779B9) & M64
        h ^= h >> 31
        h = (h * 0xBF58476D1CE4E5B9) & M64
        h ^= h >> 29
        m = self.mask
        return (h & m, (h >> 16) & m, (h >> 32) & m, (h >> 48) & m)

    def _increment(self, key):
        idx = self._hashes(key)
        r = self.rows
        for i in range(4):
            row = r[i]
            j = idx[i]
            if row[j] < 15:
                row[j] += 1
        self.samples += 1
        if self.samples >= self.reset_at:
            self.samples //= 2
            for i in range(4):
                r[i] = [v >> 1 for v in r[i]]

    def _estimate(self, key):
        a, b, c, d = self._hashes(key)
        r = self.rows
        return min(r[0][a], r[1][b], r[2][c], r[3][d])

    def access(self, key):
        self._increment(key)
        st = self.store
        if key in st:
            if key in self.win:
                self.win.move_to_end(key)
            elif key in self.prot:
                self.prot.move_to_end(key)
            else:
                del self.prob[key]
                self.prot[key] = None
                if len(self.prot) > self.pmax:
                    k, _ = self.prot.popitem(last=False)
                    self.prob[k] = None
            return True
        st[key] = True
        self.win[key] = None
        if len(self.win) > self.wmax:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mmax:
                self.prob[cand] = None
            else:
                src = self.prob if self.prob else self.prot
                if not src:
                    del st[cand]
                else:
                    vic = next(iter(src))
                    if self._estimate(cand) > self._estimate(vic):
                        del src[vic]
                        del st[vic]
                        self.prob[cand] = None
                    else:
                        del st[cand]
        return False
