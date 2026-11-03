from collections import OrderedDict


class _TLFU:
    def __init__(self, cap, wcap, protf):
        self.cap = cap; self.wcap = wcap; self.protf = protf
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.store = set()
        self.score = 0.0

    def access(self, key, f):
        if key in self.win:
            self.win.move_to_end(key); return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key] = True
            pcap = int((self.cap - self.wcap) * self.protf)
            while len(self.prot) > pcap:
                k, _ = self.prot.popitem(last=False); self.prob[k] = True
            return True
        store = self.store
        if len(store) >= self.cap and len(self.win) < self.wcap:
            self._evict_main()
        self.win[key] = True; store.add(key)
        while len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(store) <= self.cap:
                self.prob[cand] = True
                continue
            vq = self.prob if self.prob else self.prot
            victim = next(iter(vq))
            if f.get(cand, 0) > f.get(victim, 0):
                del vq[victim]; store.discard(victim); self.prob[cand] = True
            else:
                store.discard(cand)
        while len(store) > self.cap:
            self._evict_main()
        return False

    def _evict_main(self):
        vq = self.prob if self.prob else self.prot
        k, _ = vq.popitem(last=False)
        self.store.discard(k)


class Cache:
    """W-TinyLFU that copies the window size and sketch aging of its best shadow cache."""

    def __init__(self, capacity, wins=(0.01, 0.2, 0.5), prot=0.6, resets=(5, 20), halflife=5.0, period=1.0, margin=0.03, prots=(0.5, 0.8)):
        self.cap = capacity
        self.real = _TLFU(capacity, max(1, int(capacity * wins[0])), prot)
        self.real.fi = 0
        self.store = self.real.store
        self.shadows = []
        for fi in range(len(resets)):
            for w in wins:
                for p in (prots or (prot,)):
                    t = _TLFU(capacity, max(1, int(capacity * w)), p)
                    t.fi = fi
                    self.shadows.append(t)
        self.freqs = [{} for _ in resets]
        self.ops = [0] * len(resets)
        self.resets = [capacity * r for r in resets]
        self.decay = 0.5 ** (1.0 / (capacity * halflife))
        self.period = max(1, int(capacity * period)); self.n = 0
        self.cur = self.shadows[0]; self.margin = 1.0 + margin

    def access(self, key):
        fs = self.freqs
        for i in range(len(fs)):
            f = fs[i]
            v = f.get(key, 0)
            if v < 15:
                f[key] = v + 1
            self.ops[i] += 1
            if self.ops[i] >= self.resets[i]:
                self.ops[i] = 0
                fs[i] = {k: v >> 1 for k, v in f.items() if v > 1}
        d = self.decay
        for s in self.shadows:
            s.score = s.score * d + s.access(key, fs[s.fi])
        self.n += 1
        if self.n >= self.period:
            self.n = 0
            best = max(self.shadows, key=lambda s: s.score)
            if best.score > self.cur.score * self.margin:
                self.cur = best
            best = self.cur
            self.real.wcap = best.wcap
            self.real.fi = best.fi
            self.real.protf = best.protf
        return self.real.access(key, fs[self.real.fi])
