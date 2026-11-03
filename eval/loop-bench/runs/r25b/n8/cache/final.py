from collections import OrderedDict


class _TL:
    def __init__(self, cap, wfrac, pct):
        self.cap = cap; self.wcap = int(cap * wfrac); self.pct = pct
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.n = 0

    def access(self, key, f):
        if key in self.win: self.win.move_to_end(key); return True
        if key in self.prot: self.prot.move_to_end(key); return True
        hit = key in self.prob
        if hit:
            del self.prob[key]; self.prot[key] = None
        elif self.wcap:
            self.win[key] = None; self.n += 1; self.on_add(key)
        elif self.n < self.cap:
            self.prob[key] = None; self.n += 1; self.on_add(key)
        else:
            vic = next(iter(self.prob)) if self.prob else next(iter(self.prot))
            if f.get(key, 0) > f.get(vic, 0):
                if vic in self.prob: del self.prob[vic]
                else: del self.prot[vic]
                self.on_evict(vic); self.prob[key] = None; self.on_add(key)
        mcap = self.cap - self.wcap; pcap = int(mcap * self.pct)
        while len(self.prot) > pcap:
            k, _ = self.prot.popitem(last=False); self.prob[k] = None
        while len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < mcap:
                self.prob[cand] = None; continue
            vic = next(iter(self.prob)) if self.prob else next(iter(self.prot))
            if f.get(cand, 0) > f.get(vic, 0):
                if vic in self.prob: del self.prob[vic]
                else: del self.prot[vic]
                self.prob[cand] = None
            else:
                self.n -= 1; self.on_evict(cand)
                continue
            self.n -= 1; self.on_evict(vic)
        while self.n > self.cap:
            k, _ = (self.prob or self.prot).popitem(last=False); self.n -= 1; self.on_evict(k)
        return hit

    def on_evict(self, k):
        pass

    def on_add(self, k):
        pass


class _Real(_TL):
    def __init__(self, cap, wfrac, pct, store):
        _TL.__init__(self, cap, wfrac, pct); self.store = store

    def on_evict(self, k):
        self.store.discard(k)

    def on_add(self, k):
        self.store.add(k)


class Cache:
    def __init__(self, capacity, FR=(0.0, 0.01, 0.2, 0.5, 0.95), PCT=0.8, RMS=(3, 10, 30, 1000), DK=0.999):
        self.store = set()
        self.real = _Real(capacity, FR[0], PCT, self.store)
        self.resets = [int(r * capacity) for r in RMS]
        self.freqs = [{} for _ in RMS]; self.ops = 0
        self.shadows = [(j, _TL(capacity, w, PCT)) for j in range(len(RMS)) for w in FR]
        self.sc = [0.0] * len(self.shadows); self.dk = DK

    def access(self, key):
        self.ops += 1
        fs = self.freqs
        for j, f in enumerate(fs):
            v = f.get(key, 0)
            if v < 15: f[key] = v + 1
            if self.ops % self.resets[j] == 0:
                fs[j] = {a: b >> 1 for a, b in f.items() if b > 1}
        sc = self.sc; dk = self.dk; best = 0
        for i, (j, s) in enumerate(self.shadows):
            sc[i] = sc[i] * dk + s.access(key, fs[j])
            if sc[i] > sc[best]: best = i
        j, b = self.shadows[best]
        self.real.wcap = b.wcap
        hit = key in self.store
        self.real.access(key, fs[j])
        return hit
