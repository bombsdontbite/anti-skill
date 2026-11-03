from collections import OrderedDict


class _Freq:
    """Frequency counts halved every `period` requests."""

    def __init__(self, period):
        self.period = period
        self.f = {}
        self.ops = 0

    def add(self, key):
        f = self.f
        f[key] = f.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.period:
            self.ops = 0
            self.f = {k: v >> 1 for k, v in f.items() if v > 1}


class _Policy:
    """W-TinyLFU: LRU window, frequency-gated segmented LRU main."""

    def __init__(self, freq, capacity, wcap, pfrac, k=1):
        self.k = k
        self.freq = freq
        self.cap = capacity
        self.pfrac = pfrac
        self.window = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.store = set()
        self.set_wcap(wcap)

    def set_wcap(self, wcap):
        self.wcap = wcap
        self.mcap = self.cap - wcap
        self.pcap = int(self.mcap * self.pfrac)

    def resize(self, freq, wcap, pfrac):
        self.freq = freq
        self.pfrac = pfrac
        self.set_wcap(wcap)
        while len(self.prot) > self.pcap:
            k, _ = self.prot.popitem(last=False)
            self.prob[k] = True
        while len(self.window) > wcap:
            self._demote()
        while len(self.prob) + len(self.prot) > self.mcap:
            q = self.prob if self.prob else self.prot
            k, _ = q.popitem(last=False)
            self.store.discard(k)

    def _demote(self):
        cand, _ = self.window.popitem(last=False)
        if len(self.prob) + len(self.prot) < self.mcap:
            self.prob[cand] = True
            return
        vq = self.prob if self.prob else self.prot
        f = self.freq.f
        victim = None
        vf = 1 << 60
        for i, k in zip(range(self.k), vq):
            fk = f.get(k, 0)
            if fk < vf:
                victim, vf = k, fk
        if f.get(cand, 0) > vf:
            del vq[victim]
            self.store.discard(victim)
            self.prob[cand] = True
        else:
            self.store.discard(cand)

    def access(self, key):
        if key in self.window:
            self.window.move_to_end(key)
            return True
        if key in self.prot:
            self.prot.move_to_end(key)
            return True
        if key in self.prob:
            del self.prob[key]
            self.prot[key] = True
            if len(self.prot) > self.pcap:
                k, _ = self.prot.popitem(last=False)
                self.prob[k] = True
            return True
        self.window[key] = True
        self.store.add(key)
        if len(self.window) > self.wcap:
            self._demote()
        return False


class Cache:
    """W-TinyLFU that copies the window size and aging of its best recent shadow cache."""

    def __init__(self, capacity, fracs=(0.01, 0.1, 0.3, 0.6, 0.99), resets=(5, 20), decay=0.9995, pfrac=(0.5, 0.8), k=8, margin=3):
        self.margin = margin
        self.freqs = [_Freq(r * capacity) for r in resets]
        ws = sorted(set(max(1, min(capacity - 1, int(round(capacity * f)))) for f in fracs))
        self.configs = [(fi, w, p) for fi in range(len(resets)) for w in ws for p in pfrac
                        if w < ws[-1] or (fi == 0 and p == pfrac[0])]
        self.shadows = [_Policy(self.freqs[fi], capacity, w, p, k) for fi, w, p in self.configs]
        self.scores = [0.0] * len(self.configs)
        self.decay = decay
        self.best = 0
        self.real = _Policy(self.freqs[0], capacity, ws[0], pfrac[0], k)
        self.store = self.real.store

    def access(self, key):
        for fr in self.freqs:
            fr.add(key)
        sc = self.scores
        d = self.decay
        for i, s in enumerate(self.shadows):
            sc[i] = sc[i] * d + s.access(key)
        m = max(sc)
        if m > sc[self.best] + self.margin:
            self.best = sc.index(m)
        hit = self.real.access(key)
        fi, w, p = self.configs[self.best]
        if w != self.real.wcap or p != self.real.pfrac or self.freqs[fi] is not self.real.freq:
            self.real.resize(self.freqs[fi], w, p)
        return hit
