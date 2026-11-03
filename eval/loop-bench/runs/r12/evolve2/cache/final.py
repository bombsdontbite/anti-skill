from collections import OrderedDict


class _WT:
    """W-TinyLFU over a shared frequency table; window size may change."""

    def __init__(self, cap, wcap, protf):
        self.cap = cap; self.wcap = wcap; self.protf = protf
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.store = set()

    def access(self, key, f):
        if key in self.win:
            self.win.move_to_end(key); return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        prob, prot = self.prob, self.prot
        if key in prob:
            del prob[key]; prot[key] = None
            pcap = int((self.cap - self.wcap) * self.protf)
            while len(prot) > pcap:
                k, _ = prot.popitem(last=False); prob[k] = None
            return True
        cap, wcap, win, store = self.cap, self.wcap, self.win, self.store
        win[key] = None; store.add(key)
        while len(win) > wcap or len(store) > cap:
            if len(store) > cap:
                if not prob and prot:
                    k, _ = prot.popitem(last=False); prob[k] = None
                if len(win) > wcap or not prob:
                    cand, _ = win.popitem(last=False)
                    if not prob:
                        store.discard(cand); continue
                    victim = next(iter(prob))
                    if f.get(cand, 0) > f.get(victim, 0):
                        del prob[victim]; store.discard(victim); prob[cand] = None
                    else:
                        store.discard(cand)
                else:
                    victim, _ = prob.popitem(last=False); store.discard(victim)
            else:
                cand, _ = win.popitem(last=False); prob[cand] = None
        return False


class Cache:
    """W-TinyLFU that copies the window size and frequency aging of the best shadow."""

    def __init__(self, capacity, fracs=(0.01, 0.3, 0.9), ages=(5, 20),
                 prots=(0.5, 0.8), half=1.0, rate=4):
        self.cap = capacity
        self.ages = [capacity * a for a in ages]
        self.freqs = [{} for _ in ages]; self.ops = 0
        self.cfg = [(max(1, min(capacity - 1, int(capacity * x))), j, p)
                    for j in range(len(ages)) for x in fracs for p in prots]
        self.rate = rate
        sc = max(8, capacity // rate)
        self.shadows = [_WT(sc, max(1, min(sc - 1, int(sc * x))), p)
                        for j in range(len(ages)) for x in fracs for p in prots]
        self.scores = [0.0] * len(self.cfg)
        self.decay = 1.0 - rate / (capacity * half * 10)
        self.real = _WT(capacity, self.cfg[0][0], self.cfg[0][2])
        self.store = self.real.store
        self.cur = 0

    def access(self, key):
        fs = self.freqs
        for f in fs:
            f[key] = f.get(key, 0) + 1
        self.ops += 1
        for j, a in enumerate(self.ages):
            if self.ops % a == 0:
                fs[j] = {k: v >> 1 for k, v in fs[j].items() if v > 1}
        cfg = self.cfg
        if (key * 2654435761 >> 13) % self.rate == 0:
            d = self.decay; sc = self.scores
            for i, s in enumerate(self.shadows):
                sc[i] = sc[i] * d + (1.0 if s.access(key, fs[cfg[i][1]]) else 0.0)
            self.cur = sc.index(max(sc))
        w, j, p = cfg[self.cur]
        self.real.wcap = w; self.real.protf = p
        return self.real.access(key, fs[j])
