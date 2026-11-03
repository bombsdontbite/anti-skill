from collections import OrderedDict


class ARC:
    """ARC."""

    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = set()

    def _replace(self, in_b2):
        t1, t2 = self.t1, self.t2
        if t1 and (len(t1) > self.p or (in_b2 and len(t1) == self.p)):
            k, _ = t1.popitem(last=False); self.b1[k] = None
        else:
            k, _ = t2.popitem(last=False); self.b2[k] = None
        self.store.discard(k)

    def access(self, key):
        c = self.c; t1, t2, b1, b2 = self.t1, self.t2, self.b1, self.b2
        if key in t1:
            del t1[key]; t2[key] = None; return True
        if key in t2:
            t2.move_to_end(key); return True
        if key in b1:
            self.p = min(c, self.p + max(len(b2) // len(b1), 1))
            self._replace(False); del b1[key]; t2[key] = None
        elif key in b2:
            self.p = max(0, self.p - max(len(b1) // len(b2), 1))
            self._replace(True); del b2[key]; t2[key] = None
        else:
            l1 = len(t1) + len(b1)
            if l1 == c:
                if len(t1) < c:
                    b1.popitem(last=False); self._replace(False)
                else:
                    k, _ = t1.popitem(last=False); self.store.discard(k)
            elif l1 < c:
                tot = l1 + len(t2) + len(b2)
                if tot >= c:
                    if tot == 2 * c:
                        b2.popitem(last=False)
                    self._replace(False)
            t1[key] = None
        self.store.add(key)
        return False


class TinyLFU:
    """W-TinyLFU: LRU window + SLRU main, admission by a frequency sketch with aging."""

    WIN = 0.01
    PROT = 0.8

    def __init__(self, capacity, reset=10):
        self.cap = capacity
        self.wcap = max(1, int(capacity * self.WIN))
        self.mcap = capacity - self.wcap
        self.pcap = int(self.mcap * self.PROT)
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.freq = {}
        self.ops = 0
        self.reset = int(capacity * reset)
        self.store = set()

    def _inc(self, k):
        f = self.freq
        f[k] = f.get(k, 0) + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = {k: v >> 1 for k, v in f.items() if v > 1}

    def access(self, key):
        self._inc(key)
        if key in self.win:
            self.win.move_to_end(key); return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key] = None
            if len(self.prot) > self.pcap:
                k, _ = self.prot.popitem(last=False); self.prob[k] = None
            return True
        self.store.add(key)
        self.win[key] = None
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = None
            else:
                vict = next(iter(self.prob)) if self.prob else next(iter(self.prot))
                f = self.freq
                if f.get(cand, 0) > f.get(vict, 0):
                    if vict in self.prob: del self.prob[vict]
                    else: del self.prot[vict]
                    self.store.discard(vict); self.prob[cand] = None
                else:
                    self.store.discard(cand)
        return False


class Adaptive:
    """W-TinyLFU whose window size adapts ARC-style from ghost hits."""

    GW = 3.0
    GM = 0.15
    INIT = 0.05

    def __init__(self, capacity):
        self.cap = capacity
        self.w = max(1.0, capacity * self.INIT)
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.gw = OrderedDict(); self.gm = OrderedDict()
        self.freq = {}
        self.ops = 0
        self.reset = capacity * 10
        self.store = set()

    def _inc(self, k):
        f = self.freq
        f[k] = f.get(k, 0) + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = {k: v >> 1 for k, v in f.items() if v > 1}

    def _ghost(self, g, k):
        g[k] = None
        if len(g) > (self.GW * max(self.w, 1) if g is self.gw else self.GM * self.cap):
            g.popitem(last=False)

    def access(self, key):
        self._inc(key)
        win, prob, prot = self.win, self.prob, self.prot
        if key in win:
            win.move_to_end(key); return True
        if key in prot:
            prot.move_to_end(key); return True
        if key in prob:
            del prob[key]; prot[key] = None
            if len(prot) > 0.8 * (self.cap - int(self.w)):
                k, _ = prot.popitem(last=False); prob[k] = None
            return True
        cap = self.cap
        if key in self.gw:
            del self.gw[key]
            self.w = min(cap - 1.0, self.w + max(1.0, len(self.gm) / max(1, len(self.gw))))
        elif key in self.gm:
            del self.gm[key]
            self.w = max(1.0, self.w - max(1.0, len(self.gw) / max(1, len(self.gm))))
        self.store.add(key)
        win[key] = None
        wcap = int(self.w)
        while len(win) > wcap or len(win) + len(prob) + len(prot) > cap:
            if len(win) > wcap or not (prob or prot):
                cand, _ = win.popitem(last=False)
            else:
                cand = None
            if len(win) + len(prob) + len(prot) + (cand is not None) <= cap:
                prob[cand] = None
                continue
            if cand is None:
                src = prob if prob else prot
                v, _ = src.popitem(last=False)
                self.store.discard(v); self._ghost(self.gm, v)
                continue
            src = prob if prob else prot
            vict = next(iter(src)) if src else None
            f = self.freq
            if vict is not None and f.get(cand, 0) > f.get(vict, 0):
                del src[vict]; self.store.discard(vict); self._ghost(self.gm, vict)
                prob[cand] = None
            else:
                self.store.discard(cand); self._ghost(self.gw, cand)
        return False


class Cache:
    """Follow whichever shadow policy has the best recent hit rate."""

    DECAY = 10.0
    HYST = 0.005

    def __init__(self, capacity):
        self.cap = capacity
        self.shadows = [TinyLFU(capacity, 3), TinyLFU(capacity, 40), Adaptive(capacity), ARC(capacity)]
        self.ema = [0.0] * len(self.shadows)
        self.a = 1.0 / (capacity * self.DECAY)
        self.lead = 0
        self.store = set()
        self.out = []

    def access(self, key):
        st = self.store
        hit = key in st
        a = self.a; ema = self.ema
        best = 0; bv = -1.0
        for i, s in enumerate(self.shadows):
            v = ema[i] = ema[i] + a * (s.access(key) - ema[i])
            if v > bv:
                bv = v; best = i
        if bv > ema[self.lead] + self.HYST:
            self.lead = best
            ls = self.shadows[best].store
            self.out = [k for k in st if k not in ls]
        if hit:
            return True
        ls = self.shadows[self.lead].store
        if key not in ls:
            return False
        if len(st) >= self.cap:
            out = self.out
            while out:
                k = out.pop()
                if k in st and k not in ls:
                    break
            else:
                out.extend(k for k in st if k not in ls)
                k = out.pop()
            st.discard(k)
        st.add(key)
        return False
