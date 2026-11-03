from collections import OrderedDict


class Core:
    def __init__(self, cap, wcap, pfrac, fi):
        self.cap = cap; self.wcap = wcap; self.pfrac = pfrac; self.fi = fi
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.store = set()

    def access(self, key, f):
        hit = True
        if key in self.win:
            self.win.move_to_end(key)
        elif key in self.prot:
            self.prot.move_to_end(key)
        elif key in self.prob:
            del self.prob[key]; self.prot[key] = True
        else:
            hit = False
            self.win[key] = True; self.store.add(key)
        mcap = self.cap - self.wcap
        pcap = int(mcap * self.pfrac)
        prob, prot, store = self.prob, self.prot, self.store
        while len(prot) > pcap:
            k, _ = prot.popitem(last=False); prob[k] = True
        if hit and len(store) <= self.cap and len(self.win) <= self.wcap: return True
        g = f.get
        win = self.win
        while len(win) > self.wcap:
            cand, _ = win.popitem(last=False)
            if len(prob) + len(prot) < mcap:
                prob[cand] = True; continue
            vq = prob if prob else prot
            victim = next(iter(vq))
            if g(cand, 0) > g(victim, 0):
                del vq[victim]; store.discard(victim); prob[cand] = True
            else:
                store.discard(cand)
        while len(store) > self.cap:
            vq = prob if prob else (prot if prot else win)
            k, _ = vq.popitem(last=False); store.discard(k)
        return hit


class Cache:
    """W-TinyLFU whose window, protected share and frequency aging follow the best shadow cache."""

    def __init__(self, capacity, fracs=(0.01, 0.1, 0.4, 0.8), pfracs=(0.8, 0.3), resets=(5, 30, 150), decay=0.999, period=0.25, rate=4, hyst=0.01):
        self.cap = capacity
        self.freqs = [{} for _ in resets]
        self.samples = [0] * len(resets)
        self.resets = [int(capacity * r) for r in resets]
        self.rate = rate
        sc = max(4, capacity // rate)
        ws = sorted(set(max(1, min(sc - 1, round(sc * x))) for x in fracs))
        self.shadows = [Core(sc, w, p, i) for w in ws for p in pfracs for i in range(len(resets))]
        self.scale = capacity / sc
        self.scores = [0.0] * len(self.shadows)
        self.decay = decay
        self.real = Core(capacity, max(1, int(capacity * fracs[0])), pfracs[0], 0)
        self.store = self.real.store
        self.hyst = hyst
        self.cur = 0
        self.period = max(1, int(capacity * period)); self.n = 0

    def access(self, key):
        fs = self.freqs
        for i, f in enumerate(fs):
            f[key] = f.get(key, 0) + 1
            self.samples[i] += 1
            if self.samples[i] >= self.resets[i]:
                self.samples[i] //= 2
                fs[i] = {a: b >> 1 for a, b in f.items() if b > 1}
        sc = self.scores
        if (((key * 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF) >> 40) % self.rate == 0:
            d = self.decay
            for i, s in enumerate(self.shadows):
                sc[i] = sc[i] * d + s.access(key, fs[s.fi])
        self.n += 1
        if self.n >= self.period:
            self.n = 0
            best = self.cur
            for i in range(len(sc)):
                if sc[i] > sc[best]: best = i
            if sc[best] <= sc[self.cur] * (1 + self.hyst): return self.real.access(key, fs[self.real.fi])
            self.cur = best
            b = self.shadows[best]
            r = self.real
            r.wcap = max(1, min(self.cap - 1, round(b.wcap * self.scale))); r.pfrac = b.pfrac; r.fi = b.fi
        return self.real.access(key, fs[self.real.fi])
