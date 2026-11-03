from collections import OrderedDict

PROT = 0.8
FRACS = (0.01, 0.2, 0.5, 0.99)
RESETS = (5, 10, 20, 40)
DECAY = 20
MARGIN = 1.05
EXTRA = ('arc',)
LIRS_H = (0.01,)


class _TL:
    """W-TinyLFU segments; the frequency table is owned by the caller."""

    def __init__(self, cap, wcap, j):
        self.cap = cap; self.wcap = wcap; self.j = j
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.store = set(); self.ev = []

    def access(self, key, fs):
        if key in self.win:
            self.win.move_to_end(key); return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        win, prob, prot, store, ev = self.win, self.prob, self.prot, self.store, self.ev
        if key in prob:
            del prob[key]; prot[key] = None
            pcap = int((self.cap - self.wcap) * PROT)
            while len(prot) > pcap:
                k, _ = prot.popitem(last=False); prob[k] = None
            return True
        f = fs[self.j]
        win[key] = None; store.add(key)
        while len(store) > self.cap:
            if len(win) > self.wcap:
                cand, _ = win.popitem(last=False)
                vq = prob if prob else prot
                if not vq:
                    store.discard(cand); ev.append(cand); continue
                victim = next(iter(vq))
                if f.get(cand, 0) > f.get(victim, 0):
                    del vq[victim]; store.discard(victim); ev.append(victim); prob[cand] = None
                else:
                    store.discard(cand); ev.append(cand)
            else:
                vq = prob if prob else (prot if prot else win)
                k, _ = vq.popitem(last=False); store.discard(k); ev.append(k)
        while len(win) > self.wcap:
            k, _ = win.popitem(last=False); prob[k] = None
        return False


class _ARC:
    def __init__(self, c):
        self.c = c; self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = set(); self.ev = []

    def _replace(self, inb2):
        if self.t1 and (len(self.t1) > self.p or (inb2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = None
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = None
        self.store.discard(k); self.ev.append(k)

    def access(self, key, fs):
        c = self.c
        if key in self.t1:
            del self.t1[key]; self.t2[key] = None; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p = min(c, self.p + max(len(self.b2) // max(len(self.b1), 1), 1))
            self._replace(False); del self.b1[key]; self.t2[key] = None; self.store.add(key); return False
        if key in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // max(len(self.b2), 1), 1))
            self._replace(True); del self.b2[key]; self.t2[key] = None; self.store.add(key); return False
        l1 = len(self.t1) + len(self.b1)
        if l1 == c:
            if len(self.t1) < c:
                self.b1.popitem(last=False); self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False); self.store.discard(k); self.ev.append(k)
        elif l1 < c:
            tot = l1 + len(self.t2) + len(self.b2)
            if tot >= c:
                if tot == 2 * c: self.b2.popitem(last=False)
                self._replace(False)
        self.t1[key] = None; self.store.add(key); return False


class _LIRS:
    def __init__(self, c, hfrac=0.01):
        self.c = c; self.hcap = max(1, int(c * hfrac)); self.lcap = c - self.hcap
        self.S = OrderedDict()   # key -> True if LIR
        self.Q = OrderedDict()   # resident HIR
        self.nlir = 0
        self.store = set(); self.ev = []

    def _prune(self):
        S = self.S
        while S:
            k, lir = next(iter(S.items()))
            if lir: break
            S.popitem(last=False)
        if len(S) > self.c * 3:
            # bound non-resident HIR metadata
            for k in [k for k, l in S.items() if not l and k not in self.store][: len(S) - self.c * 2]:
                del S[k]

    def access(self, key, fs):
        S, Q, store = self.S, self.Q, self.store
        if key in store:
            if S.get(key):
                S.move_to_end(key); self._prune(); return True
            if key in S:
                S.move_to_end(key); S[key] = True; self.nlir += 1; del Q[key]
                k, _ = S.popitem(last=False); Q[k] = None; self.nlir -= 1
                self._prune()
            else:
                S[key] = False; Q.move_to_end(key)
            return True
        if self.nlir < self.lcap:
            S[key] = True; self.nlir += 1; store.add(key); return False
        if len(store) >= self.c:
            k, _ = Q.popitem(last=False); store.discard(k); self.ev.append(k)
        store.add(key)
        if key in S:
            S.move_to_end(key); S[key] = True; self.nlir += 1
            k, _ = S.popitem(last=False); self.nlir -= 1
            Q[k] = None
            self._prune()
        else:
            S[key] = False; Q[key] = None
        return False


class _LRU:
    def __init__(self, c):
        self.c = c; self.d = OrderedDict(); self.store = self.d; self.ev = []

    def access(self, key, fs):
        d = self.d
        if key in d:
            d.move_to_end(key); return True
        if len(d) >= self.c:
            k, _ = d.popitem(last=False); self.ev.append(k)
        d[key] = None; return False


class Cache:
    """Runs several shadow policies and makes its own contents follow the recent best one."""

    def __init__(self, capacity):
        self.cap = capacity
        self.resets = [capacity * r for r in RESETS]
        self.freqs = [{} for _ in RESETS]; self.ns = [0] * len(RESETS)
        self.shadows = [_TL(capacity, max(1, min(capacity - 1, int(capacity * x))), j)
                        for x in FRACS for j in range(len(RESETS))]
        if 'arc' in EXTRA: self.shadows.append(_ARC(capacity))
        for h in LIRS_H: self.shadows.append(_LIRS(capacity, h))
        if 'lru' in EXTRA: self.shadows.append(_LRU(capacity))
        self.score = [0.0] * len(self.shadows)
        self.decay = 1.0 - 1.0 / (capacity * DECAY)
        self.lead = 0
        self.store = set(); self.diff = set()

    def access(self, key):
        fs = self.freqs
        for j, f in enumerate(fs):
            f[key] = f.get(key, 0) + 1
            self.ns[j] += 1
            if self.ns[j] >= self.resets[j]:
                self.ns[j] //= 2
                fs[j] = {a: b >> 1 for a, b in f.items() if b > 1}
        store = self.store; diff = self.diff
        hit = key in store
        sc = self.score; d = self.decay
        best = self.lead
        for i, s in enumerate(self.shadows):
            sc[i] = sc[i] * d + s.access(key, fs)
            if sc[i] > sc[best]: best = i
        lead = self.shadows[self.lead]
        for s in self.shadows:
            if s is lead:
                for k in s.ev:
                    if k in store: diff.add(k)
            s.ev.clear()
        if best != self.lead and sc[best] > sc[self.lead] * MARGIN:
            self.lead = best; lead = self.shadows[best]
            ls = lead.store
            self.diff = diff = {k for k in store if k not in ls}
        if key in lead.store:
            diff.discard(key)
            if not hit:
                if len(store) >= self.cap:
                    store.discard(diff.pop())
                store.add(key)
        return hit
