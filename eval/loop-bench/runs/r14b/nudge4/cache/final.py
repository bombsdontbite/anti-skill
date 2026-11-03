from collections import OrderedDict


class _Seg:
    """W-TinyLFU body: LRU window, then frequency-gated segmented LRU."""

    def __init__(self, capacity, wfrac, pfrac, freq):
        self.capacity = capacity
        self.freq = freq
        self.store = set()
        self.window = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.resize(wfrac, pfrac)

    def resize(self, wfrac, pfrac):
        self.wfrac, self.pfrac = wfrac, pfrac
        cap = self.capacity
        self.wcap = min(cap, max(1, int(round(cap * wfrac))))
        self.mcap = cap - self.wcap
        self.pcap = int(self.mcap * pfrac)
        while len(self.window) > self.wcap:
            k, _ = self.window.popitem(last=False)
            self.prob[k] = True
        while len(self.prob) + len(self.prot) > self.mcap:
            k, _ = (self.prob or self.prot).popitem(last=False)
            self.store.discard(k)
        while len(self.prot) > self.pcap:
            k, _ = self.prot.popitem(last=False)
            self.prob[k] = True

    def access(self, key):
        if key in self.window:
            self.window.move_to_end(key)
            return True
        prot = self.prot
        if key in prot:
            prot.move_to_end(key)
            return True
        prob = self.prob
        if key in prob:
            del prob[key]
            prot[key] = True
            if len(prot) > self.pcap:
                k, _ = prot.popitem(last=False)
                prob[k] = True
            return True
        store = self.store
        store.add(key)
        self.window[key] = True
        if len(self.window) > self.wcap:
            cand, _ = self.window.popitem(last=False)
            if len(prob) + len(prot) < self.mcap:
                prob[cand] = True
            elif not (prob or prot):
                store.discard(cand)
            else:
                victim = next(iter(prob or prot))
                f = self.freq
                if f.get(cand, 0) > f.get(victim, 0):
                    del (prob if victim in prob else prot)[victim]
                    store.discard(victim)
                    prob[cand] = True
                else:
                    store.discard(cand)
        return False


class Cache:
    """W-TinyLFU whose window, protected size and frequency aging follow the best shadow cache."""

    WFRACS = (0.01, 0.05, 0.2, 0.5, 1.0)
    PFRACS = (0.5, 0.8)
    SAMPLES = (3, 10, 30, 100)
    CAP = 15
    DECAY = 0.999
    EVERY = 0.25
    MARGIN = 5.0

    def __init__(self, capacity):
        self.freqs = [{} for _ in self.SAMPLES]
        self.resets = [max(1, s * capacity) for s in self.SAMPLES]
        self.ops = 0
        self.params = [(w, p, j) for w in self.WFRACS for p in self.PFRACS
                       for j in range(len(self.SAMPLES))]
        self.shadows = [_Seg(capacity, w, p, self.freqs[j]) for w, p, j in self.params]
        self.scores = [0.0] * len(self.shadows)
        self.cur = self.params[0]
        self.main = _Seg(capacity, self.cur[0], self.cur[1], self.freqs[self.cur[2]])
        self.store = self.main.store
        self.every = max(1, int(capacity * self.EVERY))
        self.n = 0

    def access(self, key):
        cap = self.CAP
        for f in self.freqs:
            v = f.get(key, 0)
            if v < cap:
                f[key] = v + 1
        hit = self.main.access(key)
        sc = self.scores
        d = self.DECAY
        for i, s in enumerate(self.shadows):
            sc[i] = sc[i] * d + s.access(key)
        self.ops += 1
        for f, r in zip(self.freqs, self.resets):
            if self.ops % r == 0:
                for k in list(f):
                    v = f[k] >> 1
                    if v:
                        f[k] = v
                    else:
                        del f[k]
        self.n += 1
        if self.n >= self.every:
            self.n = 0
            b = max(range(len(sc)), key=sc.__getitem__)
            best = self.params[b]
            if best != self.cur and sc[b] > sc[self.params.index(self.cur)] + self.MARGIN:
                self.cur = best
                m = self.main
                m.freq = self.freqs[best[2]]
                m.resize(best[0], best[1])
        return hit
