from collections import OrderedDict


class LIRS:
    def __init__(self, capacity, hir=0.03, smul=10):
        self.c = capacity
        self.hir_cap = max(1, int(capacity * hir))
        self.lir_cap = capacity - self.hir_cap
        self.S = OrderedDict(); self.Q = OrderedDict()
        self.lir = set(); self.store = set()
        self.maxS = capacity * smul
        self.ev = None

    def _prune(self):
        S, lir = self.S, self.lir
        while S:
            k = next(iter(S))
            if k in lir: break
            del S[k]

    def access(self, key):
        S, Q, lir, st = self.S, self.Q, self.lir, self.store
        if key in lir:
            S.move_to_end(key); self._prune(); return True
        if key in st:
            if key in S:
                lir.add(key); del Q[key]; S.move_to_end(key)
                k = next(iter(S)); lir.discard(k); del S[k]; Q[k] = None
                self._prune()
            else:
                S[key] = None; Q.move_to_end(key)
            return True
        if len(lir) < self.lir_cap and len(st) < self.c:
            lir.add(key); st.add(key); S[key] = None; return False
        if len(st) >= self.c:
            k, _ = Q.popitem(last=False); st.discard(k)
            if self.ev is not None: self.ev.append(k)
        st.add(key)
        if key in S:
            lir.add(key); S.move_to_end(key)
            k = next(iter(S)); lir.discard(k); del S[k]; Q[k] = None
            self._prune()
        else:
            S[key] = None; Q[key] = None
        if len(S) > self.maxS:
            for k in S:
                if k not in lir and k not in st:
                    del S[k]; break
        return False


class ARC:
    def __init__(self, capacity):
        self.c = capacity; self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = set(); self.ev = None

    def _replace(self, inb2):
        if self.t1 and (len(self.t1) > self.p or (inb2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = None
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = None
        self.store.discard(k)
        if self.ev is not None: self.ev.append(k)

    def access(self, key):
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
                k, _ = self.t1.popitem(last=False); self.store.discard(k)
                if self.ev is not None: self.ev.append(k)
        else:
            tot = l1 + len(self.t2) + len(self.b2)
            if tot >= c:
                if tot == 2 * c and self.b2:
                    self.b2.popitem(last=False)
                if len(self.t1) + len(self.t2) >= c:
                    self._replace(False)
        self.t1[key] = None; self.store.add(key)
        return False


class TLFU:
    def __init__(self, capacity, w=0.01, r=10):
        self.c = capacity
        self.wc = max(1, int(capacity * w))
        self.mc = capacity - self.wc
        self.pc = max(1, int(self.mc * 0.8))
        self.W = OrderedDict(); self.P = OrderedDict(); self.Pr = OrderedDict()
        self.f = {}; self.n = 0; self.reset = capacity * r
        self.store = set(); self.ev = None

    def access(self, key):
        f = self.f
        f[key] = f.get(key, 0) + 1
        self.n += 1
        if self.n >= self.reset:
            self.n = 0
            f = self.f = {a: b >> 1 for a, b in f.items() if b > 1}
        if key in self.W:
            self.W.move_to_end(key); return True
        if key in self.Pr:
            self.Pr.move_to_end(key); return True
        if key in self.P:
            del self.P[key]; self.Pr[key] = None
            if len(self.Pr) > self.pc:
                k, _ = self.Pr.popitem(last=False); self.P[k] = None
            return True
        st = self.store
        st.add(key); self.W[key] = None
        if len(self.W) > self.wc:
            cand, _ = self.W.popitem(last=False)
            if len(self.P) + len(self.Pr) < self.mc:
                self.P[cand] = None
            else:
                vict = next(iter(self.P)) if self.P else next(iter(self.Pr))
                if f.get(cand, 0) > f.get(vict, 0):
                    if vict in self.P: del self.P[vict]
                    else: del self.Pr[vict]
                    self.P[cand] = None
                    cand = vict
                st.discard(cand)
                if self.ev is not None: self.ev.append(cand)
        return False


class Cache:
    """Follow the shadow policy with the best recent hit rate."""

    DECAY = 0.9997

    def __init__(self, capacity):
        self.c = capacity
        self.experts = [LIRS(capacity, 0.01), ARC(capacity), TLFU(capacity), LIRS(capacity, 0.2), TLFU(capacity, 0.01, 80)]
        self.score = [0.0] * len(self.experts)
        self.lead = 0
        self.pend = []
        self.experts[0].ev = self.pend
        self.store = set()
        self.t = 0

    def access(self, key):
        st = self.store
        hit = key in st
        sc = self.score; d = self.DECAY
        for i, e in enumerate(self.experts):
            sc[i] = sc[i] * d + (1.0 if e.access(key) else 0.0)
        lead = self.experts[self.lead]
        self.t += 1
        if self.t % 64 == 0:
            b = self.lead
            for i in range(len(sc)):
                if sc[i] > sc[b] * 1.02 + 1.0: b = i
            if b != self.lead:
                lead.ev = None
                self.lead = b; lead = self.experts[b]
                ls = lead.store
                self.pend = [k for k in st if k not in ls]
                lead.ev = self.pend
        if hit:
            return True
        ls = lead.store
        if key not in ls:
            return False
        if len(st) >= self.c:
            pend = self.pend
            while True:
                if pend:
                    k = pend.pop()
                    if k in st and k not in ls:
                        st.discard(k); break
                else:
                    for k in st:
                        if k not in ls: break
                    st.discard(k); break
        st.add(key)
        return False
