from collections import OrderedDict

FRACS = (0.01, 0.1, 0.35, 0.8)
STALES = (1e9, 2, 4)


class _WTLFU:
    """W-TinyLFU over a shared frequency table; window size may change."""

    def __init__(self, capacity, wcap, store, stale=1e9, pshare=0.8):
        self.pshare = pshare
        self.capacity = capacity
        self.wcap = wcap
        self.store = store
        self.window = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.stale = capacity * stale

    def _evict_main(self):
        if self.prob:
            k, _ = self.prob.popitem(last=False)
        else:
            k, _ = self.prot.popitem(last=False)
        del self.store[k]

    def access(self, key, f, last, now):
        store = self.store
        if key in store:
            if key in self.window:
                self.window.move_to_end(key)
            elif key in self.prob:
                del self.prob[key]
                self.prot[key] = True
                pcap = int((self.capacity - self.wcap) * self.pshare)
                while len(self.prot) > pcap:
                    k, _ = self.prot.popitem(last=False)
                    self.prob[k] = True
            else:
                self.prot.move_to_end(key)
            return True
        store[key] = True
        self.window[key] = True
        while len(self.window) > self.wcap:
            cand, _ = self.window.popitem(last=False)
            if len(store) <= self.capacity:
                self.prob[cand] = True
                continue
            victim = next(iter(self.prob)) if self.prob else next(iter(self.prot))
            if f.get(cand, 0) > f.get(victim, 0) or now - last[victim] > self.stale:
                self._evict_main()
                self.prob[cand] = True
            else:
                del store[cand]
        if len(store) > self.capacity:
            self._evict_main()
        return False


class Cache:
    def __init__(self, capacity, period_mult=2.0, decay=0.8, reset_mult=10):
        self.capacity = capacity
        self.store = {}
        self.freq = {}
        self.ops = 0
        self.reset_at = capacity * reset_mult
        wc = [min(capacity - 1, max(1, int(capacity * fr))) for fr in FRACS]
        self.shadows = [_WTLFU(capacity, w, {}, st, ps) for ps in (0.8, 0.45, 0.15) for st in STALES for w in wc]
        self.score = [0.0] * len(self.shadows)
        self.real = _WTLFU(capacity, wc[0], self.store)
        self.period = max(1, int(capacity * period_mult))
        self.decay = decay
        self.n = 0
        self.last = {}
        self.t = 0

    def access(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.reset_at:
            self.ops = 0
            self.freq = f = {k: v >> 1 for k, v in f.items() if v > 1}
        self.t += 1
        t = self.t
        last = self.last
        sc = self.score
        for i, s in enumerate(self.shadows):
            if s.access(key, f, last, t):
                sc[i] += 1
        self.n += 1
        if self.n >= self.period:
            self.n = 0
            best = max(range(len(sc)), key=lambda i: sc[i])
            self.real.wcap = self.shadows[best].wcap
            self.real.stale = self.shadows[best].stale
            self.real.pshare = self.shadows[best].pshare
            d = self.decay
            self.score = [x * d for x in sc]
        hit = self.real.access(key, f, last, t)
        last[key] = t
        return hit
