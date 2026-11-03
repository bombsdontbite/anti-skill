from collections import OrderedDict


class _TLFU:
    """W-TinyLFU: LRU window, SLRU main, admission by frequency."""

    def __init__(self, capacity, wcap, prot_frac):
        self.cap = capacity
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.store = set()
        self.set_mode(wcap, prot_frac)

    def set_mode(self, wcap, prot_frac):
        self.wcap = wcap
        self.mcap = self.cap - wcap
        self.pcap = int(self.mcap * prot_frac)

    def access(self, key, f):
        win = self.win
        if key in win:
            win.move_to_end(key); return True
        prot = self.prot
        if key in prot:
            prot.move_to_end(key); return True
        prob = self.prob
        if key in prob:
            del prob[key]; prot[key] = None
            while len(prot) > self.pcap:
                prob[prot.popitem(last=False)[0]] = None
            return True
        store = self.store
        store.add(key)
        win[key] = None
        mcap = self.mcap
        while len(win) > self.wcap:
            cand = win.popitem(last=False)[0]
            if len(prob) + len(prot) < mcap:
                prob[cand] = None
                continue
            vq = prob if prob else prot
            victim = next(iter(vq))
            if f.get(cand, 0) > f.get(victim, 0):
                del vq[victim]; store.discard(victim)
                prob[cand] = None
            else:
                store.discard(cand)
        while len(prob) + len(prot) > mcap:
            store.discard((prob if prob else prot).popitem(last=False)[0])
        return False


class Cache:
    """W-TinyLFU whose window and protected share follow the best of three shadow caches."""

    def __init__(self, capacity, small=0.01, big=0.99, half=1.0, margin=0.02,
                 reset_mult=10, fcap=15, prots=(0.8, 0.3)):
        self.cap = capacity
        small = max(1, int(capacity * small))
        big = min(capacity - 1, max(small, int(capacity * big)))
        self.modes = [(small, p) for p in prots] + [(big, prots[0])]
        self.real = _TLFU(capacity, small, prots[0])
        self.store = self.real.store
        self.sh = [_TLFU(capacity, small, p) for p in prots]
        self.sc = [0.0] * len(self.modes)
        self.cur = 0
        self.lru = OrderedDict()
        self.a = 1.0 / (capacity * half)
        self.margin = margin
        self.freq = {}
        self.ops = 0
        self.reset_at = capacity * reset_mult
        self.fcap = fcap

    def access(self, key):
        f = self.freq
        v = f.get(key, 0)
        if v < self.fcap:
            f[key] = v + 1
        self.ops += 1
        if self.ops >= self.reset_at:
            self.ops = 0
            self.freq = f = {k: v >> 1 for k, v in f.items() if v > 1}
        a = self.a
        sc = self.sc
        i = 0
        for s in self.sh:
            sc[i] += a * ((1.0 if s.access(key, f) else 0.0) - sc[i])
            i += 1
        lru = self.lru
        if key in lru:
            lru.move_to_end(key); h = 1.0
        else:
            h = 0.0
            lru[key] = None
            if len(lru) > self.cap:
                lru.popitem(last=False)
        sc[i] += a * (h - sc[i])
        best = 0
        for j in range(1, i + 1):
            if sc[j] > sc[best]:
                best = j
        if best != self.cur and sc[best] > sc[self.cur] + self.margin:
            self.cur = best
            self.real.set_mode(*self.modes[best])
        return self.real.access(key, f)
