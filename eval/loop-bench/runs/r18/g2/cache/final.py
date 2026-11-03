from collections import OrderedDict



class Lirs:
    """LIRS whose resident-HIR share grows while a shadow LRU out-hits it."""

    def __init__(self, capacity, hir_frac=0.03, ghost_mult=3.0, epoch_mult=1.0, step=0.05,
                 lo=0.01, hi=0.3, margin=0.0):
        self.margin = margin
        self.lru = OrderedDict(); self.lru_hits = 0
        self.c = capacity
        self.frac = hir_frac
        self.lo, self.hi = lo, hi
        self.step = step
        self.dir = 1
        self.epoch = max(100, int(capacity * epoch_mult))
        self.n = 0; self.hits = 0; self.prev = -1.0
        self.lcap = capacity - max(1, int(capacity * hir_frac))
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.G = OrderedDict()
        self.gmax = max(1, int(capacity * ghost_mult))
        self.store = {}
        self.nlir = 0

    def _prune(self):
        S, G = self.S, self.G
        while S:
            k = next(iter(S))
            if S[k]:
                return
            del S[k]
            if k in G:
                del G[k]

    def _demote_bottom(self):
        k, _ = self.S.popitem(last=False)
        self.nlir -= 1
        self.Q[k] = True
        self._prune()

    def _climb(self):
        if self.lru_hits > self.hits * (1 + self.margin) + 2:
            f = self.frac + self.step
        elif self.hits > self.lru_hits * (1 + self.margin) + 2:
            f = self.frac - self.step
        else:
            f = self.frac
        f = min(self.hi, max(self.lo, f))
        self.n = self.hits = self.lru_hits = 0
        self.frac = f
        self.lcap = self.c - max(1, int(self.c * f))

    def _hit(self, key):
        S, Q = self.S, self.Q
        if key in S:
            if S[key]:
                first = next(iter(S)) == key
                S.move_to_end(key)
                if first:
                    self._prune()
                return
            S[key] = True; S.move_to_end(key); del Q[key]; self.nlir += 1
            self._demote_bottom()
        else:
            S[key] = False; Q.move_to_end(key)

    def access(self, key):
        self.n += 1
        if self.n >= self.epoch:
            self._climb()
        lru = self.lru
        if key in lru:
            lru.move_to_end(key); self.lru_hits += 1
        else:
            lru[key] = True
            if len(lru) > self.c:
                lru.popitem(last=False)
        st = self.store
        if key in st:
            self.hits += 1
            self._hit(key)
            return True
        S, Q = self.S, self.Q
        while self.nlir > self.lcap:
            self._demote_bottom()
        if len(st) >= self.c:
            if not Q:
                self._demote_bottom()
            k, _ = Q.popitem(last=False); del st[k]
            if k in S:
                G = self.G
                G[k] = True
                if len(G) > self.gmax:
                    g, _ = G.popitem(last=False); del S[g]
        st[key] = True
        if key in self.G:
            del self.G[key]
        if self.nlir < self.lcap:
            S[key] = True; S.move_to_end(key); self.nlir += 1
        elif key in S:
            S[key] = True; S.move_to_end(key); self.nlir += 1
            self._demote_bottom()
        else:
            S[key] = False; Q[key] = True
        return False



class Hawk:
    """Hawkeye-style: OPTgen on recent history labels each key friendly/averse."""

    def __init__(self, capacity, win_mult=8, nq=128, init=3, thr=4, mru=False):
        self.mru = mru
        self.c = capacity
        self.q = max(1, capacity * win_mult // nq)
        self.nq = nq
        self.occ = [0] * nq
        self.t = 0
        self.last = {}  # key -> time of last access (within window)
        self.pred = {}
        self.init = init; self.thr = thr
        self.fr = OrderedDict(); self.av = OrderedDict()
        self.store = {}

    def _optgen(self, key):
        t = self.t
        q, nq, occ = self.q, self.nq, self.occ
        cur = t // q
        if t % q == 0:
            occ[cur % nq] = 0
        t0 = self.last.get(key)
        self.last[key] = t
        if t0 is None:
            return None
        p = t0 // q
        if cur - p >= nq - 1:
            return False
        a, b = p % nq, cur % nq
        if a <= b:
            seg = occ[a:b]
            if seg and max(seg) >= self.c:
                return False
            for i in range(a, b):
                occ[i] += 1
        else:
            if max(max(occ[a:], default=0), max(occ[:b], default=0)) >= self.c:
                return False
            for i in range(a, nq):
                occ[i] += 1
            for i in range(b):
                occ[i] += 1
        return True

    def access(self, key):
        self.t += 1
        if self.t % (self.c * 64) == 0:
            lim = self.t - self.q * self.nq
            self.last = {k: v for k, v in self.last.items() if v > lim}
        res = self._optgen(key)
        pr = self.pred
        p = pr.get(key, self.init)
        if res is True:
            p = min(7, p + 1)
        elif res is False:
            p = max(0, p - 1)
        pr[key] = p
        friendly = p >= self.thr
        st, fr, av = self.store, self.fr, self.av
        if key in st:
            if key in fr: del fr[key]
            else: del av[key]
            (fr if friendly else av)[key] = True
            return True
        if len(st) >= self.c:
            if av:
                k, _ = av.popitem(last=self.mru)
            else:
                k, _ = fr.popitem(last=False)
                pr[k] = max(0, pr.get(k, self.init) - 1)
            del st[k]
        st[key] = True
        (fr if friendly else av)[key] = True
        return False



class TinyLfu:
    def __init__(self, capacity):
        self.c = capacity
        self.wcap = max(1, capacity // 100)
        self.mcap = capacity - self.wcap
        self.pcap = int(self.mcap * 0.8)
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.freq = {}
        self.ops = 0; self.reset = capacity * 10
        self.store = {}

    def _inc(self, k):
        f = self.freq
        f[k] = f.get(k, 0) + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = {a: b >> 1 for a, b in f.items() if b > 1}

    def access(self, key):
        self._inc(key)
        if key in self.win:
            self.win.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key] = True
            if len(self.prot) > self.pcap:
                k, _ = self.prot.popitem(last=False); self.prob[k] = True
            return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        self.win[key] = True; self.store[key] = True
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = True
            else:
                vq = self.prob if self.prob else self.prot
                victim = next(iter(vq))
                f = self.freq
                if f.get(cand, 0) > f.get(victim, 0):
                    del vq[victim]; del self.store[victim]; self.prob[cand] = True
                else:
                    del self.store[cand]
        return False


class Cache:
    """Follows whichever shadow policy has the most recent hits (decayed)."""

    def __init__(self, capacity, decay=1 - 1 / 20000, experts=(Lirs, Hawk, TinyLfu), m=0.97):
        self.m = m
        self.c = capacity
        self.ex = [E(capacity) for E in experts]
        self.sc = [0.0] * len(self.ex)
        self.d = decay if decay is not None else 1.0 - 1.0 / (2 * capacity)
        self.best = 0
        self.order = OrderedDict()
        self.store = self.order

    def access(self, key):
        sc, d = self.sc, self.d
        for i, e in enumerate(self.ex):
            sc[i] = sc[i] * d + e.access(key)
        b = self.best
        if sc[b] < max(sc) * self.m:
            b = self.best = sc.index(max(sc))
        st = self.order
        if key in st:
            st.move_to_end(key)
            return True
        bs = self.ex[b].store
        if key not in bs:
            return False
        if len(st) >= self.c:
            for k in st:
                if k not in bs:
                    break
            else:
                k = next(iter(st))
            del st[k]
        st[key] = True
        return False
