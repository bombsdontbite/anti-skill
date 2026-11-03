from collections import OrderedDict


class _W:
    """W-TinyLFU over a shared frequency table; evicted keys are logged in `ev`."""

    def __init__(self, c, wcap, pfrac):
        self.c = c; self.wcap = wcap; self.pcap = int((c - wcap) * pfrac)
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.store = {}; self.ev = []

    def access(self, key, f):
        if key in self.win:
            self.win.move_to_end(key); return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key] = True
            if len(self.prot) > self.pcap:
                k, _ = self.prot.popitem(last=False); self.prob[k] = True
            return True
        self.win[key] = True; self.store[key] = True
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.c - self.wcap:
                self.prob[cand] = True
            elif not (self.prob or self.prot):
                del self.store[cand]; self.ev.append(cand)
            else:
                q = self.prob or self.prot
                victim = next(iter(q))
                if f.get(cand, 0) > f.get(victim, 0):
                    del q[victim]; del self.store[victim]; self.ev.append(victim)
                    self.prob[cand] = True
                else:
                    del self.store[cand]; self.ev.append(cand)
        return False


class _WA:
    """W-TinyLFU that also admits over a main victim untouched for `age` requests."""

    def __init__(self, c, wcap, pfrac, age):
        self.w = _W(c, wcap, pfrac); self.store = self.w.store; self.ev = self.w.ev
        self.age = age; self.last = {}; self.t = 0

    def access(self, key, f):
        self.t += 1
        last = self.last; t = self.t
        if key in self.store:
            last[key] = t
            return self.w.access(key, f)
        w = self.w
        if len(w.win) >= w.wcap and (w.prob or w.prot) and \
                len(w.prob) + len(w.prot) >= w.c - w.wcap:
            q = w.prob or w.prot
            victim = next(iter(q))
            if t - last.get(victim, t) > self.age:
                f = {victim: -1}
        r = self.w.access(key, f)
        last[key] = t
        for k in self.ev:
            last.pop(k, None)
        return r


class _Arc:
    """ARC; evicted keys are logged in `ev`."""

    def __init__(self, c):
        self.c = c; self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = {}; self.ev = []

    def _replace(self, in_b2):
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        del self.store[k]; self.ev.append(k)

    def access(self, key, f):
        c = self.c
        if key in self.t1:
            del self.t1[key]; self.t2[key] = True; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p = min(c, self.p + max(len(self.b2) // len(self.b1), 1))
            self._replace(False); del self.b1[key]; self.t2[key] = True; self.store[key] = True
            return False
        if key in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // len(self.b2), 1))
            self._replace(True); del self.b2[key]; self.t2[key] = True; self.store[key] = True
            return False
        l1 = len(self.t1) + len(self.b1)
        if l1 == c:
            if len(self.t1) < c:
                self.b1.popitem(last=False); self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False); del self.store[k]; self.ev.append(k)
        else:
            tot = l1 + len(self.t2) + len(self.b2)
            if tot >= c:
                if tot == 2 * c:
                    self.b2.popitem(last=False)
                self._replace(False)
        self.t1[key] = True; self.store[key] = True
        return False


class _F:
    """Frequency table, halved every `period` requests."""

    def __init__(self, period):
        self.f = {}; self.ops = 0; self.period = period

    def add(self, key):
        f = self.f
        v = f.get(key, 0)
        if v < 15: f[key] = v + 1
        self.ops += 1
        if self.ops >= self.period:
            self.ops = 0
            self.f = {k: v >> 1 for k, v in f.items() if v > 1}


class Cache:
    """Runs several shadow caches and keeps the contents of the one with the most recent hits."""

    FRACS = (0.01, 0.2, 0.6)
    PFRACS = (0.5,)
    RESETS = (3, 24)
    ARC = True
    AGES = (2,)

    def __init__(self, capacity, period=0.5, keep=0.95, margin=0.05):
        c = capacity
        self.c = c
        self.freqs = [_F(r * c) for r in self.RESETS]
        self.cfg = [(max(1, min(c - 1, int(c * x))), p, j)
                    for j in range(len(self.RESETS)) for p in self.PFRACS for x in self.FRACS]
        self.shadows = [_W(c, w, p) for w, p, j in self.cfg]
        self.fidx = [j for w, p, j in self.cfg]
        for a in self.AGES:
            self.shadows.append(_WA(c, max(1, c // 100), 0.5, a * c)); self.fidx.append(0); self.cfg.append(None)
        if self.ARC:
            self.shadows.append(_Arc(c)); self.fidx.append(0); self.cfg.append(None)
        self.score = [0.0] * len(self.cfg)
        self.lead = 0
        self.store = {}
        self.stale = OrderedDict()
        self.period = max(16, int(period * c)); self.n = 0; self.keep = keep; self.margin = margin

    def access(self, key):
        for F in self.freqs: F.add(key)
        fs = [F.f for F in self.freqs]
        sc = self.score
        fidx = self.fidx
        i = 0
        for s in self.shadows:
            if s.access(key, fs[fidx[i]]): sc[i] += 1
            i += 1
        lead = self.shadows[self.lead]
        store = self.store; stale = self.stale
        for k in lead.ev:
            if k in store: stale[k] = True
        for s in self.shadows: s.ev.clear()
        if key in store:
            hit = True
        else:
            hit = False
            if key in lead.store:
                store[key] = True
                if len(store) > self.c:
                    if stale:
                        k, _ = stale.popitem(last=False)
                    else:
                        k = next(iter(store))
                    del store[k]
        self.n += 1
        if self.n >= self.period:
            self.n = 0
            best = sc.index(max(sc))
            if best != self.lead and sc[best] > sc[self.lead] * (1 + self.margin) + 1:
                self.lead = best
                ls = self.shadows[best].store
                self.stale = OrderedDict((k, True) for k in store if k not in ls)
            k = self.keep
            self.score = [x * k for x in sc]
        return hit
