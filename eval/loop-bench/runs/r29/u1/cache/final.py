from collections import OrderedDict

SHAPES = ((0.01, 0), (0.2, 0), (0.99, 0))
RESETS = (100,)
PROT = 0.8
DEC = 4
FMAX = 15
MARG = 0.04
CHECK = 8
KAPPA = 0.35
HIRS = (0.01,)


class WT:
    """W-TinyLFU body: window LRU, then an SLRU main gated by frequency."""

    def __init__(self, capacity, wcap):
        self.c = capacity
        self.wcap = wcap
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.store = set()

    def access(self, key, f):
        win, prob, prot = self.win, self.prob, self.prot
        if key in win:
            win.move_to_end(key); return True
        if key in prot:
            prot.move_to_end(key); return True
        if key in prob:
            del prob[key]; prot[key] = True
            if len(prot) > int((self.c - self.wcap) * PROT):
                k, _ = prot.popitem(last=False); prob[k] = True
            return True
        win[key] = True; self.store.add(key)
        if len(win) > self.wcap:
            cand, _ = win.popitem(last=False)
            if len(prob) + len(prot) < self.c - self.wcap:
                prob[cand] = True
            else:
                q = prob if prob else prot
                victim = next(iter(q))
                if f.get(cand, 0) > f.get(victim, 0):
                    del q[victim]; self.store.discard(victim); prob[cand] = True
                else:
                    self.store.discard(cand)
        return False


class LIRS:
    """LIRS (shadow)."""

    def __init__(self, capacity, hfrac=0.01):
        self.hcap = max(1, int(capacity * hfrac))
        self.lcap = capacity - self.hcap
        self.s = OrderedDict(); self.q = OrderedDict()
        self.lir = set(); self.store = set()

    def _prune(self):
        s, lir = self.s, self.lir
        while s:
            k = next(iter(s))
            if k in lir:
                break
            del s[k]

    def _demote(self):
        s = self.s
        k, _ = s.popitem(last=False)
        self.lir.discard(k); self.q[k] = True
        self._prune()

    def access(self, key, f):
        s, q, lir, store = self.s, self.q, self.lir, self.store
        if key in lir:
            s[key] = True; s.move_to_end(key)
            self._prune()
            return True
        if key in store:
            if key in s:
                s.move_to_end(key); del q[key]; lir.add(key)
                self._demote()
            else:
                s[key] = True; q.move_to_end(key)
            return True
        if len(lir) < self.lcap:
            lir.add(key); s[key] = True; s.move_to_end(key); store.add(key)
            return False
        if len(q) >= self.hcap:
            k, _ = q.popitem(last=False); store.discard(k)
        store.add(key)
        if key in s:
            s.move_to_end(key); lir.add(key)
            self._demote()
        else:
            s[key] = True; q[key] = True
        return False


class Freq:
    """Saturating access counts, halved every `period` requests."""

    def __init__(self, period):
        self.f = {}
        self.ops = 0
        self.period = period

    def add(self, key):
        f = self.f
        v = f.get(key, 0)
        if v < FMAX:
            f[key] = v + 1
        self.ops += 1
        if self.ops >= self.period:
            self.ops = 0
            self.f = {k: v >> 1 for k, v in f.items() if v > 1}


class Cache:
    """Holds the keys of whichever shadow policy has the best recent hit rate."""

    def __init__(self, capacity):
        self.c = capacity
        self.freqs = [Freq(r * capacity) for r in RESETS]
        self.shadows = [WT(capacity, min(capacity - 1, max(1, int(capacity * x)))) for x, _ in SHAPES]
        self.fidx = [j for _, j in SHAPES]
        self.shadows += [LIRS(capacity, h) for h in HIRS]
        self.fidx += [0] * len(HIRS)
        self.score = [0.0] * len(self.shadows)
        self.decay = 1.0 - 1.0 / (DEC * capacity)
        self.lead = 0
        self.marg = MARG * DEC * capacity
        self.t = 0
        self.store = OrderedDict()

    def access(self, key):
        for fr in self.freqs:
            fr.add(key)
        fs = [fr.f for fr in self.freqs]
        d = self.decay; sc = self.score; fidx = self.fidx
        for i, s in enumerate(self.shadows):
            sc[i] = sc[i] * d + s.access(key, fs[fidx[i]])
        st = self.store
        self.t += 1
        if self.t >= CHECK:
            # Switching costs about one miss per key the new leader holds and we do not.
            self.t = 0
            lead = self.lead
            best = lead
            for i in range(len(sc)):
                if sc[i] > sc[best]:
                    best = i
            gain = sc[best] - sc[lead]
            if best != lead and gain > self.marg:
                bs = self.shadows[best].store
                diff = 0
                for k in bs:
                    if k not in st:
                        diff += 1
                if gain > self.marg + KAPPA * diff:
                    self.lead = best
        if key in st:
            st.move_to_end(key)
            return True
        ls = self.shadows[self.lead].store
        if key in ls:
            if len(st) >= self.c:
                while True:
                    k = next(iter(st))
                    if k in ls:
                        st.move_to_end(k)
                    else:
                        del st[k]
                        break
            st[key] = True
        return False
