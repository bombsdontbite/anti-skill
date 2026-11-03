from collections import OrderedDict


class _WTiny:
    """W-TinyLFU over a frequency table owned by the caller."""

    def __init__(self, capacity, wcap, stale=None):
        self.capacity = capacity
        self.stale = stale * capacity if stale else None
        self.wcap = wcap
        self.window = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.score = 0.0

    def resize(self, wcap):
        self.wcap = wcap
        while len(self.window) > wcap:
            k, _ = self.window.popitem(last=False)
            self.prob[k] = True
        mcap = self.capacity - wcap
        while len(self.prob) + len(self.prot) > mcap:
            k, _ = (self.prob or self.prot).popitem(last=False)
            if len(self.window) < wcap:
                self.window[k] = True
                self.window.move_to_end(k, last=False)
        pcap = int(mcap * 0.8)
        while len(self.prot) > pcap:
            k, _ = self.prot.popitem(last=False)
            self.prob[k] = True

    def access(self, key, f, last, now):
        """Returns (hit, evicted key or None, whether key was stored)."""
        if key in self.window:
            self.window.move_to_end(key)
            return True, None, True
        if key in self.prot:
            self.prot.move_to_end(key)
            return True, None, True
        if key in self.prob:
            del self.prob[key]
            self.prot[key] = True
            if len(self.prot) > int((self.capacity - self.wcap) * 0.8):
                k, _ = self.prot.popitem(last=False)
                self.prob[k] = True
            return True, None, True
        self.window[key] = True
        if len(self.window) <= self.wcap:
            return False, None, True
        cand, _ = self.window.popitem(last=False)
        if len(self.prob) + len(self.prot) < self.capacity - self.wcap:
            self.prob[cand] = True
            return False, None, True
        st = self.stale
        if st and self.prot:
            victim = next(iter(self.prot))
            if now - last.get(victim, now) > st:
                del self.prot[victim]
                self.prob[cand] = True
                return False, victim, True
        main = self.prob or self.prot
        victim = next(iter(main))
        if f.get(cand, 0) > f.get(victim, 0) or (st and now - last.get(victim, now) > st):
            del main[victim]
            self.prob[cand] = True
            return False, victim, True
        return False, cand, cand != key


class _Freq:
    """Saturating counters, halved every `reset` requests."""

    def __init__(self, reset, fmax):
        self.f = {}
        self.reset = reset
        self.fmax = fmax
        self.ops = 0

    def add(self, key):
        f = self.f
        c = f.get(key, 0)
        if c < self.fmax:
            f[key] = c + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.f = {k: v >> 1 for k, v in f.items() if v > 1}


class Cache:
    """W-TinyLFU whose window size and aging follow the best of several shadow caches."""

    def __init__(self, capacity, resets=(16,), fracs=(0.01, 0.2, 0.8),
                 fmax=15, decay=0.9995, period=50, stales=(None, 2)):
        self.capacity = capacity
        self.freqs = [_Freq(capacity * r, fmax) for r in resets]
        wsizes = sorted({min(capacity - 1, max(1, int(capacity * x))) for x in fracs})
        self.shadows = [(_WTiny(capacity, w, st), fr)
                        for st in stales for fr in self.freqs for w in wsizes]
        self.last = {}
        self.now = 0
        self.real = _WTiny(capacity, wsizes[0])
        self.rfreq = self.freqs[-1]
        self.store = {}
        self.decay = decay
        self.period = period
        self.tick = 0

    def access(self, key):
        now = self.now = self.now + 1
        last = self.last
        for fr in self.freqs:
            fr.add(key)
        for s, fr in self.shadows:
            if s.access(key, fr.f, last, now)[0]:
                s.score += 1.0
        self.tick += 1
        if self.tick >= self.period:
            self.tick = 0
            d = self.decay ** self.period
            for s, _ in self.shadows:
                s.score *= d
            best, self.rfreq = max(self.shadows, key=lambda p: p[0].score)
            self.real.stale = best.stale
            if best.wcap != self.real.wcap:
                self.real.resize(best.wcap)
                self._sync()
        hit, out, stored = self.real.access(key, self.rfreq.f, last, now)
        last[key] = now
        if not hit:
            if stored:
                self.store[key] = True
            if out is not None and out != key:
                del self.store[out]
        return hit

    def _sync(self):
        r = self.real
        live = set(r.window) | set(r.prob) | set(r.prot)
        for k in [k for k in self.store if k not in live]:
            del self.store[k]
