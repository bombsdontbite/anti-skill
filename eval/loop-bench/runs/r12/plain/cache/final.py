from collections import OrderedDict


class Cache:
    """W-TinyLFU whose window adapts ARC-style from ghost hits.

    A window-ghost hit grows the window only if the key's reuse distance
    (distinct keys since its last access) fits in the cache.
    """

    def __init__(self, capacity):
        self.cap = capacity
        self.w = max(1.0, capacity * 0.01)
        self.win = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.gw = OrderedDict()
        self.gm = OrderedDict()
        self.freq = {}
        self.last = {}
        self.ops = 0
        self.t = 0
        self.reset = capacity * 10
        self.marks = bytearray(1 << 16)
        self.blocks = [0] * (1 << 8)
        self.store = set()

    def _distance(self, prev):
        t, marks, blocks = self.t, self.marks, self.blocks
        lo, hi = prev + 1, t
        bl, bh = lo >> 8, hi >> 8
        if bl == bh:
            return sum(marks[lo:hi])
        d = sum(marks[lo:(bl + 1) << 8]) + sum(marks[bh << 8:hi])
        for b in range(bl + 1, bh):
            d += blocks[b]
        return d

    def _ghost(self, g, key):
        g[key] = True
        if len(g) > self.cap:
            g.popitem(last=False)

    def access(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops //= 2
            self.freq = f = {k: v >> 1 for k, v in f.items() if v > 1}
        t = self.t
        marks = self.marks
        if t >= len(marks):
            marks.extend(bytearray(len(marks)))
            self.blocks.extend([0] * len(self.blocks))
        prev = self.last.get(key, -1)
        if prev >= 0:
            marks[prev] = 0
            self.blocks[prev >> 8] -= 1
        marks[t] = 1
        self.blocks[t >> 8] += 1
        self.last[key] = t
        self.t = t + 1
        if key in self.win:
            self.win.move_to_end(key)
            return True
        if key in self.prot:
            self.prot.move_to_end(key)
            return True
        prob, prot, win = self.prob, self.prot, self.win
        cap = self.cap
        if key in prob:
            del prob[key]
            prot[key] = True
            if len(prot) > max(1, int((cap - len(win)) * 0.8)):
                k, _ = prot.popitem(last=False)
                prob[k] = True
            return True
        if key in self.gw:
            del self.gw[key]
            if self._distance(prev) <= cap * SPAN:
                self.w = min(cap - 1.0, self.w + max(1.0, len(self.gm) / max(1, len(self.gw))) * GAIN)
        elif key in self.gm:
            del self.gm[key]
            self.w = max(1.0, self.w - max(1.0, len(self.gw) / max(1, len(self.gm))) * GAIN)
        self.w = max(1.0, self.w - DRIFT)
        wcap = int(self.w)
        mcap = cap - wcap
        win[key] = True
        self.store.add(key)
        while len(win) > wcap:
            cand, _ = win.popitem(last=False)
            if len(prob) + len(prot) < mcap:
                prob[cand] = True
                continue
            src = prob if prob else prot
            if not src:
                self.store.discard(cand)
                continue
            victim = next(iter(src))
            if f.get(cand, 0) > f.get(victim, 0):
                del src[victim]
                self.store.discard(victim)
                self._ghost(self.gm, victim)
                prob[cand] = True
            else:
                self.store.discard(cand)
                self._ghost(self.gw, cand)
        while len(win) + len(prob) + len(prot) > cap:
            src = prob if prob else prot
            k, _ = src.popitem(last=False)
            self.store.discard(k)
            self._ghost(self.gm, k)
        return False


GAIN = 1.0
SPAN = 1.0
DRIFT = 0.05
