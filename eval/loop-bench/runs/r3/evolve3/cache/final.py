from collections import OrderedDict


class Lru:
    def __init__(self, capacity):
        self.cap = capacity
        self.store = OrderedDict(); self.ad = []; self.ev = []

    def access(self, key):
        s = self.store
        if key in s:
            s.move_to_end(key); return True
        if len(s) >= self.cap:
            k, _ = s.popitem(last=False); self.ev.append(k)
        s[key] = True; self.ad.append(key)
        return False


class Lirs:
    def __init__(self, capacity, hfrac=0.01, smul=20):
        self.cap = capacity
        self.hcap = max(1, int(capacity * hfrac))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict(); self.Q = OrderedDict(); self.lir = set()
        self.store = set(); self.smax = capacity * smul
        self.ad = []; self.ev = []

    def _prune(self):
        S = self.S; lir = self.lir
        while S:
            k = next(iter(S))
            if k in lir: break
            del S[k]

    def _bound(self):
        S = self.S
        while len(S) > self.smax:
            k = next(iter(S))
            if k in self.lir:
                del S[k]; self.lir.discard(k); self.Q[k] = True
                self._prune()
                if len(self.Q) > self.hcap:
                    v, _ = self.Q.popitem(last=False); self.store.discard(v); self.ev.append(v)
            else:
                del S[k]

    def access(self, key):
        S, Q, lir = self.S, self.Q, self.lir
        if key in lir:
            bottom = next(iter(S)) == key
            S.move_to_end(key)
            if bottom: self._prune()
            return True
        if key in self.store:
            if key in S:
                del Q[key]; S.move_to_end(key); lir.add(key)
                b = next(iter(S)); del S[b]; lir.discard(b); Q[b] = True
                self._prune()
            else:
                S[key] = False; Q.move_to_end(key)
            self._bound()
            return True
        self.ad.append(key)
        if len(lir) < self.lcap:
            lir.add(key); S[key] = True; S.move_to_end(key); self.store.add(key)
            return False
        if len(self.store) >= self.cap:
            v, _ = Q.popitem(last=False); self.store.discard(v); self.ev.append(v)
        self.store.add(key)
        if key in S:
            S.move_to_end(key); lir.add(key)
            b = next(iter(S)); del S[b]; lir.discard(b); Q[b] = True
            self._prune()
        else:
            S[key] = False; Q[key] = True
        self._bound()
        return False


class Tlfu2:
    """W-TinyLFU with exact aged counts instead of a sketch."""

    def __init__(self, capacity, wfrac=0.01, pfrac=0.8, resetmul=10, cmax=15, tie=False):
        self.wcap = max(1, int(capacity * wfrac))
        self.mcap = capacity - self.wcap
        self.pcap = int(self.mcap * pfrac)
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.store = set(); self.ad = []; self.ev = []
        self.f = {}; self.n = 0; self.reset = capacity * resetmul; self.cmax = cmax; self.tie = tie

    def access(self, key):
        f = self.f
        c = f.get(key, 0)
        if c < self.cmax: f[key] = c + 1
        self.n += 1
        if self.n >= self.reset:
            self.n //= 2
            self.f = {k: v >> 1 for k, v in f.items() if v > 1}
        if key in self.win:
            self.win.move_to_end(key); return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key] = True
            if len(self.prot) > self.pcap:
                k, _ = self.prot.popitem(last=False); self.prob[k] = True
            return True
        self.store.add(key); self.win[key] = True; self.ad.append(key)
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = True
            else:
                vic = next(iter(self.prob)) if self.prob else next(iter(self.prot))
                fc = self.f.get(cand, 0); fv = self.f.get(vic, 0)
                if fc > fv or (self.tie and fc == fv):
                    if vic in self.prob: del self.prob[vic]
                    else: del self.prot[vic]
                    self.store.discard(vic); self.ev.append(vic); self.prob[cand] = True
                else:
                    self.store.discard(cand); self.ev.append(cand)
        return False


WIN = 10.0
HYST = 0.0
Z = 1.0


class Hyb:
    """Follow-the-leader over shadow policies; real store drifts toward the leader's."""

    def __init__(self, capacity, experts=("lirs", "tlfu2", "lru", ("tlfu2", {"resetmul": 30}), ("lirs", {"hfrac": 0.1})), win=WIN, hyst=HYST, z=Z):
        self.cap = capacity
        mk = {"lirs": Lirs, "lru": Lru, "tlfu2": Tlfu2}
        self.ex = [mk[n[0]](capacity, **n[1]) if isinstance(n, tuple) else mk[n](capacity) for n in experts]
        self.D = [OrderedDict() for _ in self.ex]
        self.sc = [0.0 for _ in self.ex]
        self.d = 1.0 - 1.0 / (win * capacity)
        self.hyst = hyst; self.z = z
        self.lead = 0
        self.store = set()

    def access(self, key):
        R = self.store
        hit = key in R
        d = self.d; sc = self.sc; D = self.D
        for i, e in enumerate(self.ex):
            h = e.access(key)
            sc[i] = sc[i] * d + (1.0 if h else 0.0)
            Di = D[i]
            if e.ad:
                for x in e.ad:
                    if x in Di: del Di[x]
                e.ad.clear()
            if e.ev:
                for x in e.ev:
                    if x in R: Di[x] = True
                e.ev.clear()
        L = self.lead
        best = L
        for i in range(len(sc)):
            if sc[i] > sc[best]: best = i
        if best != L and sc[best] - sc[L] > self.hyst * sc[L] + self.z * (sc[best] + sc[L] + 1.0) ** 0.5:
            L = self.lead = best
        if not hit:
            SL = self.ex[L].store
            if key in SL or len(R) < self.cap:
                if len(R) >= self.cap:
                    x, _ = D[L].popitem(last=False)
                    R.discard(x)
                    for Dj in D:
                        if x in Dj: del Dj[x]
                R.add(key)
                for j, e in enumerate(self.ex):
                    if key not in e.store: D[j][key] = True
        return hit


class Cache(Hyb):
    pass
