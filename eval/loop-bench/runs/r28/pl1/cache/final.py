from collections import OrderedDict


class _Sim:
    """W-TinyLFU over a shared frequency table, with a resizable window."""

    def __init__(self, capacity, wcap, prot, owner):
        self.capacity = capacity
        self.ti = 0
        self.wcap = wcap
        self.prot_frac = prot
        self.owner = owner
        self.win = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.score = 0.0

    def resize(self, wcap):
        self.wcap = wcap
        mcap = self.capacity - wcap
        while len(self.win) > wcap:
            k, _ = self.win.popitem(last=False)
            self.prob[k] = True
        while len(self.prob) + len(self.prot) > mcap:
            q = self.prob if self.prob else self.prot
            k, _ = q.popitem(last=False)
            self.win[k] = True
            self.win.move_to_end(k, last=False)
        self._fix_prot()

    def _fix_prot(self):
        pcap = int((self.capacity - self.wcap) * self.prot_frac)
        while len(self.prot) > pcap:
            k, _ = self.prot.popitem(last=False)
            self.prob[k] = True

    def access(self, key, store):
        if key in self.win:
            self.win.move_to_end(key)
            return True
        if key in self.prot:
            self.prot.move_to_end(key)
            return True
        if key in self.prob:
            del self.prob[key]
            self.prot[key] = True
            self._fix_prot()
            return True
        self.win[key] = True
        if store is not None:
            store.add(key)
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.capacity - self.wcap:
                self.prob[cand] = True
            else:
                vq = self.prob if self.prob else self.prot
                victim = next(iter(vq))
                f = self.owner.freqs[self.ti]
                if f.get(cand, 0) > f.get(victim, 0):
                    del vq[victim]
                    if store is not None:
                        store.discard(victim)
                    self.prob[cand] = True
                elif store is not None:
                    store.discard(cand)
        return False


class Cache:
    """W-TinyLFU whose window size and frequency aging follow the best shadow configuration."""

    FRACS = (0.01, 0.05, 0.15, 0.3, 0.5, 0.75, 0.99)
    SAMPLES = (2, 5, 12, 30, 80)

    def __init__(self, capacity, prot=0.8, period=1.0, keep=0.9):
        self.capacity = capacity
        self.freqs = [{} for _ in self.SAMPLES]
        self.resets = [s * capacity for s in self.SAMPLES]
        self.ops = 0
        self.store = set()
        sizes = [min(capacity - 1, max(1, int(capacity * f))) for f in self.FRACS]
        self.ghosts = []
        for ti in range(len(self.SAMPLES)):
            for w in sizes:
                g = _Sim(capacity, w, prot, self)
                g.ti = ti
                self.ghosts.append(g)
        self.real = _Sim(capacity, sizes[0], prot, self)
        self.real.ti = 1
        self.period = max(1, int(period * capacity))
        self.keep = keep
        self.n = 0

    def access(self, key):
        self.ops += 1
        freqs = self.freqs
        for i, r in enumerate(self.resets):
            f = freqs[i]
            f[key] = f.get(key, 0) + 1
            if self.ops % r == 0:
                freqs[i] = {k: v >> 1 for k, v in f.items() if v > 1}
        for g in self.ghosts:
            if g.access(key, None):
                g.score += 1.0
        hit = self.real.access(key, self.store)
        self.n += 1
        if self.n >= self.period:
            self.n = 0
            best = max(self.ghosts, key=lambda g: g.score)
            self.real.ti = best.ti
            if best.wcap != self.real.wcap:
                self.real.resize(best.wcap)
            for g in self.ghosts:
                g.score *= self.keep
        return hit
