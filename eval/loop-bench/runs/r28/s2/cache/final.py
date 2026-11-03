from collections import OrderedDict


class LIRS:
    def __init__(self, capacity, ev, hfrac=0.01):
        self.hcap = max(1, int(capacity * hfrac))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict(); self.Q = OrderedDict()
        self.lir = set(); self.res = set()
        self.nlimit = capacity * 3
        self.ev = ev

    def _prune(self):
        S, lir = self.S, self.lir
        while S:
            k = next(iter(S))
            if k in lir: break
            del S[k]

    def _demote(self):
        S = self.S
        k = next(iter(S)); self.lir.discard(k); del S[k]; self.Q[k] = True; self._prune()

    def access(self, key):
        S, Q, lir = self.S, self.Q, self.lir
        if key in lir:
            S.move_to_end(key); self._prune(); return True
        if key in self.res:
            if key in S:
                del S[key]; S[key] = True; del Q[key]; lir.add(key); self._demote()
            else:
                S[key] = True; Q.move_to_end(key)
            return True
        self.res.add(key)
        if len(lir) < self.lcap and not Q:
            lir.add(key); S[key] = True; return False
        if len(Q) >= self.hcap:
            k, _ = Q.popitem(last=False); self.res.discard(k); self.ev(k)
        if key in S:
            del S[key]; S[key] = True; lir.add(key); self._demote()
        else:
            S[key] = True; Q[key] = True
        if len(S) > self.lcap + self.nlimit:
            res = self.res
            for k in list(S):
                if len(S) <= self.lcap + self.nlimit // 2: break
                if k not in res: del S[k]
        return False


class ARC:
    def __init__(self, capacity, ev):
        self.c = capacity; self.p = 0; self.ev = ev
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()

    def _replace(self, in_b2):
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        self.ev(k)

    def access(self, key):
        c = self.c
        if key in self.t1:
            del self.t1[key]; self.t2[key] = True; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p = min(c, self.p + max(len(self.b2) // max(len(self.b1), 1), 1))
            self._replace(False); del self.b1[key]; self.t2[key] = True; return False
        if key in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // max(len(self.b2), 1), 1))
            self._replace(True); del self.b2[key]; self.t2[key] = True; return False
        l1 = len(self.t1) + len(self.b1)
        if l1 == c:
            if len(self.t1) < c:
                self.b1.popitem(last=False); self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False); self.ev(k)
        elif l1 < c:
            tot = l1 + len(self.t2) + len(self.b2)
            if tot >= c:
                if tot == 2 * c and self.b2:
                    self.b2.popitem(last=False)
                self._replace(False)
        self.t1[key] = True
        return False


class TLFU:
    def __init__(self, capacity, ev):
        self.wcap = max(1, capacity // 100)
        self.mcap = capacity - self.wcap
        self.pcap = max(1, int(self.mcap * 0.8))
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.freq = {}; self.ops = 0; self.reset = capacity * 80; self.ev = ev

    def access(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = f = {a: b >> 1 for a, b in f.items() if b > 1}
        if key in self.win:
            self.win.move_to_end(key); return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key] = True
            if len(self.prot) > self.pcap:
                k, _ = self.prot.popitem(last=False); self.prob[k] = True
            return True
        self.win[key] = True
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = True
            else:
                victim = next(iter(self.prob)) if self.prob else next(iter(self.prot))
                if f.get(cand, 0) > f.get(victim, 0):
                    if victim in self.prob: del self.prob[victim]
                    else: del self.prot[victim]
                    self.ev(victim); self.prob[cand] = True
                else:
                    self.ev(cand)
        return False


class Cache:
    """Follow whichever simulated policy has more recent hits; evict real keys it would not hold."""

    DECAY = 0.9995
    HYST = 1.05

    def __init__(self, capacity):
        self.cap = capacity
        self.store = OrderedDict()
        self.diffs = []
        self.sims = []
        for mk in (lambda ev: LIRS(capacity, ev), lambda ev: ARC(capacity, ev), lambda ev: TLFU(capacity, ev)):
            d = OrderedDict(); self.diffs.append(d)
            self.sims.append(mk(self._mkev(d)))
        self.scores = [0.0] * len(self.sims)
        self.cur = 0

    def _mkev(self, d):
        store = self.store
        def ev(k):
            if k in store: d[k] = True
        return ev

    def access(self, key):
        sc = self.scores; dec = self.DECAY
        for i, s in enumerate(self.sims):
            sc[i] = sc[i] * dec + s.access(key)
            self.diffs[i].pop(key, None)
        store = self.store
        if key in store:
            store.move_to_end(key); return True
        if len(store) >= self.cap:
            w = self.cur
            for i in range(len(sc)):
                if sc[i] > sc[w] * self.HYST + 1.0:
                    w = i
            self.cur = w
            d = self.diffs[w]
            if d:
                k, _ = d.popitem(last=False)
            else:
                k = next(iter(store))
            del store[k]
            for o in self.diffs: o.pop(k, None)
        store[key] = True
        return False
