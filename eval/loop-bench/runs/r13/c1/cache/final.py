from collections import OrderedDict


class LRU:
    def __init__(self, capacity):
        self.cap = capacity
        self.store = OrderedDict()
        self.ev = []

    def access(self, key):
        s = self.store
        if key in s:
            s.move_to_end(key); return True
        if len(s) >= self.cap:
            k, _ = s.popitem(last=False); self.ev.append(k)
        s[key] = None
        return False


class TinyLFU:
    """W-TinyLFU; with adapt, the window grows/shrinks ARC-style on ghost hits."""

    def __init__(self, capacity, adapt, reset, win=0.01, fmax=15):
        self.cap = capacity
        self.adapt = adapt
        self.wcap = max(1.0, capacity * win)
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.gw = OrderedDict(); self.gm = OrderedDict()
        self.gmax = max(1, capacity // 2); self.gwmax = max(1, capacity // 10)
        self.freq = {}
        self.fmax = fmax
        self.ops = 0
        self.reset = capacity * reset
        self.store = set()
        self.ev = []

    def access(self, key):
        f = self.freq
        v = f.get(key, 0)
        if v < self.fmax:
            f[key] = v + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = f = {k: v >> 1 for k, v in f.items() if v > 1}
        if key in self.win:
            self.win.move_to_end(key); return True
        prot = self.prot
        if key in prot:
            prot.move_to_end(key); return True
        prob = self.prob
        if key in prob:
            del prob[key]; prot[key] = None
            pcap = int((self.cap - self.wcap) * 0.8)
            while len(prot) > pcap:
                k, _ = prot.popitem(last=False); prob[k] = None
            return True
        cap = self.cap
        if self.adapt:
            gw = self.gw; gm = self.gm
            if key in gw:
                del gw[key]
                self.wcap = min(cap - 1.0, self.wcap + max(1.0, len(gm) / max(1, len(gw))))
            elif key in gm:
                del gm[key]
                self.wcap = max(1.0, self.wcap - max(1.0, len(gw) / max(1, len(gm))))
        store = self.store
        store.add(key)
        win = self.win
        win[key] = None
        wcap = int(self.wcap)
        ev = self.ev
        while len(win) > wcap or len(store) > cap:
            if len(store) > cap and len(win) <= wcap:
                vd = prob if prob else prot
                victim, _ = vd.popitem(last=False); store.discard(victim); ev.append(victim)
                self._ghost(self.gm, victim, self.gmax)
                continue
            cand, _ = win.popitem(last=False)
            if len(store) <= cap:
                prob[cand] = None
                continue
            vd = prob if prob else prot
            victim = next(iter(vd))
            if f.get(cand, 0) > f.get(victim, 0):
                del vd[victim]; store.discard(victim); prob[cand] = None; ev.append(victim)
                self._ghost(self.gm, victim, self.gmax)
            else:
                store.discard(cand); ev.append(cand)
                self._ghost(self.gw, cand, self.gwmax)
        return False

    def _ghost(self, g, k, m):
        if self.adapt:
            g[k] = None
            if len(g) > m:
                g.popitem(last=False)


class LIRS:
    def __init__(self, capacity, hfrac=0.01):
        self.cap = capacity
        self.hcap = max(1, int(capacity * hfrac))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict()  # recency stack, last = top
        self.Q = OrderedDict()  # resident HIR, first = next victim
        self.st = {}  # key -> 0 LIR, 1 resident HIR, 2 non-resident HIR (only while in S)
        self.nl = 0
        self.store = set()
        self.ev = []

    def _prune(self):
        S = self.S; st = self.st
        while S:
            k = next(iter(S))
            if st[k] == 0:
                return
            del S[k]
            if st[k] == 2:
                del st[k]

    def _demote(self):
        S = self.S
        k, _ = S.popitem(last=False)
        self.st[k] = 1; self.Q[k] = None
        self._prune()

    def access(self, key):
        S = self.S; Q = self.Q; st = self.st
        x = st.get(key)
        if x == 0:
            bottom = next(iter(S)) == key
            S.move_to_end(key)
            if bottom:
                self._prune()
            return True
        if x == 1:
            if key in S:
                st[key] = 0; S.move_to_end(key); del Q[key]
                self._demote()
            else:
                S[key] = None; Q.move_to_end(key)
            return True
        store = self.store
        if len(store) >= self.cap:
            v, _ = Q.popitem(last=False)
            store.discard(v); self.ev.append(v)
            if v in S:
                st[v] = 2
            else:
                del st[v]
        store.add(key)
        if self.nl < self.lcap:
            self.nl += 1; st[key] = 0
            S.pop(key, None); S[key] = None
            return False
        if x == 2:
            st[key] = 0; S.move_to_end(key)
            self._demote()
        else:
            st[key] = 1; S[key] = None; Q[key] = None
        if len(S) > 4 * self.cap:
            for k in list(S)[:self.cap]:
                if st[k] == 2:
                    del S[k]; del st[k]
            self._prune()
        return False


class Cache:
    """Runs several policies as shadows and evicts toward whichever has hit most recently."""

    def __init__(self, capacity, decay=4.0, margin=25.0):
        self.cap = capacity
        self.experts = [LRU(capacity), TinyLFU(capacity, False, 100), TinyLFU(capacity, True, 4), LIRS(capacity)]
        n = len(self.experts)
        self.score = [0.0] * n
        self.decay = 1.0 - 1.0 / (decay * capacity)
        self.margin = margin
        self.lead = 1
        self.diff = [OrderedDict() for _ in range(n)]  # cached keys this expert does not hold
        self.store = set()

    def access(self, key):
        store = self.store
        hit = key in store
        score = self.score; d = self.decay; diff = self.diff
        for i, e in enumerate(self.experts):
            s = score[i] * d
            if e.access(key):
                s += 1.0
            score[i] = s
            di = diff[i]
            if e.ev:
                for k in e.ev:
                    if k in store:
                        di[k] = None
                e.ev.clear()
            if key in e.store:
                di.pop(key, None)
        lead = self.lead
        best = lead
        for i in range(len(score)):
            if score[i] > score[best]:
                best = i
        if best != lead and score[best] > score[lead] + self.margin:
            self.lead = lead = best
        if hit:
            return True
        le = self.experts[lead]
        if key not in le.store:
            return False
        if len(store) >= self.cap:
            dl = diff[lead]
            v, _ = dl.popitem(last=False)
            store.discard(v)
            for di in diff:
                di.pop(v, None)
        store.add(key)
        for i, e in enumerate(self.experts):
            if key not in e.store:
                diff[i][key] = None
        return False
