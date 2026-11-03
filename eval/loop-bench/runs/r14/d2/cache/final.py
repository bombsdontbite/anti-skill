import random
from collections import OrderedDict


class _TLFU:
    def __init__(self, cap, wcap, pfrac):
        self.cap = cap; self.wcap = wcap; self.pfrac = pfrac
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.store = set()
        self.score = 0.0
        self.ev = []

    def access(self, key, f):
        if key in self.store:
            if key in self.win:
                self.win.move_to_end(key)
            elif key in self.prot:
                self.prot.move_to_end(key)
            else:
                del self.prob[key]; self.prot[key] = None
                if len(self.prot) > self.pcap:
                    k, _ = self.prot.popitem(last=False); self.prob[k] = None
            return True
        self.win[key] = None; self.store.add(key)
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.store) <= self.cap:
                self.prob[cand] = None
                return False
            vq = self.prob if self.prob else self.prot
            victim = next(iter(vq))
            if f.get(cand, 0) > f.get(victim, 0):
                del vq[victim]; self.prob[cand] = None
                cand = victim
            self.store.discard(cand); self.ev.append(cand)
        return False


class _LIRS:

    def __init__(self, capacity, hfrac=0.01, nr=3.0):
        self.cap = capacity
        self.hcap = max(1, int(capacity * hfrac))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict()   # key -> is LIR
        self.Q = OrderedDict()
        self.nres = OrderedDict()
        self.nrcap = int(nr * capacity)
        self.nlir = 0
        self.store = set()
        self.ev = []
        self.score = 0.0

    def _prune(self):
        S = self.S
        while S:
            k, lir = next(iter(S.items()))
            if lir:
                return
            S.popitem(last=False)
            self.nres.pop(k, None)

    def _demote(self):
        k, _ = self.S.popitem(last=False)
        self.Q[k] = None
        self._prune()

    def access(self, key, f=None):
        S = self.S; Q = self.Q
        if key in self.store:
            if S.get(key):
                first = next(iter(S)) == key
                S.move_to_end(key)
                if first:
                    self._prune()
            elif key in S:
                S[key] = True; S.move_to_end(key); del Q[key]
                self._demote()
            else:
                S[key] = False; Q.move_to_end(key)
            return True
        if len(self.store) >= self.cap:
            if Q:
                v, _ = Q.popitem(last=False)
            else:
                v = next(iter(S)); del S[v]; self.nlir -= 1; self._prune()
            self.store.discard(v); self.ev.append(v)
            if v in S:
                self.nres[v] = None
                if len(self.nres) > self.nrcap:
                    o, _ = self.nres.popitem(last=False)
                    S.pop(o, None)
                    self._prune()
        self.store.add(key)
        if self.nlir < self.lcap:
            S.pop(key, None); self.nres.pop(key, None)
            S[key] = True; self.nlir += 1
        elif key in S:
            del self.nres[key]
            S[key] = True; S.move_to_end(key)
            self._demote()
        else:
            S[key] = False; Q[key] = None
        return False


class _ARC:

    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = set()
        self.ev = []
        self.score = 0.0

    def _replace(self, in_b2):
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = None
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = None
        self.store.discard(k); self.ev.append(k)

    def access(self, key, f=None):
        c = self.c
        if key in self.t1:
            del self.t1[key]; self.t2[key] = None; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p = min(c, self.p + max(len(self.b2) // len(self.b1), 1))
            self._replace(False); del self.b1[key]; self.t2[key] = None
        elif key in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // len(self.b2), 1))
            self._replace(True); del self.b2[key]; self.t2[key] = None
        else:
            l1 = len(self.t1) + len(self.b1)
            if l1 == c:
                if len(self.t1) < c:
                    self.b1.popitem(last=False); self._replace(False)
                else:
                    k, _ = self.t1.popitem(last=False); self.store.discard(k); self.ev.append(k)
            elif l1 < c:
                tot = l1 + len(self.t2) + len(self.b2)
                if tot >= c:
                    if tot == 2 * c:
                        self.b2.popitem(last=False)
                    self._replace(False)
            self.t1[key] = None
        self.store.add(key)
        return False


class _Pred:

    def __init__(self, capacity, n=32, hist=8, seed=1, bypass=True, unk=4.0, a=1.0):
        self.cap = capacity
        self.n = n
        self.keys = []; self.pos = {}
        self.last = {}; self.iv = {}
        self.t = 0
        self.hist = hist * capacity
        self.unk = unk * capacity
        self.bypass = bypass
        self.a = a
        self.rng = random.Random(seed)
        self.store = self.pos
        self.ev = []
        self.score = 0.0

    def _nxt(self, k, t):
        iv = self.iv.get(k)
        l = self.last[k]
        if iv is None:
            return l + self.unk if l + self.unk > t else t + (t - l)
        p = l + iv
        return p if p > t else t + (t - l)

    def access(self, key, f=None):
        self.t += 1
        t = self.t
        l = self.last.get(key)
        if l is not None:
            o = self.iv.get(key)
            self.iv[key] = t - l if o is None else o + self.a * (t - l - o)
        self.last[key] = t
        if key in self.pos:
            return True
        if len(self.last) > self.hist + self.cap:
            cut = t - self.hist
            self.last = {k: v for k, v in self.last.items() if v > cut or k in self.pos}
            self.iv = {k: v for k, v in self.iv.items() if k in self.last}
        if len(self.keys) >= self.cap:
            keys = self.keys; rr = self.rng.randrange; m = len(keys)
            best = None; bv = -1
            for _ in range(self.n):
                k = keys[rr(m)]
                v = self._nxt(k, t)
                if v > bv:
                    best = k; bv = v
            if self.bypass and self._nxt(key, t) > bv:
                return False
            i = self.pos.pop(best); last = keys.pop()
            if last is not best:
                keys[i] = last; self.pos[last] = i
            self.ev.append(best)
        self.pos[key] = len(self.keys); self.keys.append(key)
        return False


class Cache:
    """Follows whichever shadow cache (W-TinyLFU at several window sizes and agings, LIRS, ARC, reuse-interval) has had the most recent hits."""

    def __init__(self, capacity, fracs=(0.01, 0.1, 0.3, 0.6, 0.99), pfrac=0.8, decay=None, resets=(10, 40), fmax=15, hfracs=(0.01, 0.1), dk=128, vote=32, arc=1, margin=0.01, pred=1):
        self.cap = capacity
        self.shadows = []
        self.freqs = [{} for _ in resets]
        self.periods = [r * capacity for r in resets]
        for i in range(len(resets)):
            for x in fracs:
                s = _TLFU(capacity, min(capacity - 1, max(1, int(capacity * x))), pfrac)
                s.pcap = int((capacity - s.wcap) * pfrac)
                s.fi = i
                self.shadows.append(s)
        for h in hfracs:
            s = _LIRS(capacity, h); s.fi = 0
            self.shadows.append(s)
        for _ in range(arc):
            s = _ARC(capacity); s.fi = 0
            self.shadows.append(s)
        for _ in range(pred):
            s = _Pred(capacity); s.fi = 0
            self.shadows.append(s)
        self.best = self.shadows[0]
        self.store = set()
        self.extra = set()
        self.ops = 0
        self.fmax = fmax
        self.decay = decay if decay is not None else 1.0 - 1.0 / (dk * capacity)
        self.inc = 1.0
        self.vote = vote
        self.margin = 1.0 + margin
        self.switches = 0

    def access(self, key):
        self.ops += 1
        fs = self.freqs
        for i, f in enumerate(fs):
            v = f.get(key, 0)
            if v < self.fmax:
                f[key] = v + 1
            if self.ops % self.periods[i] == 0:
                fs[i] = {a: b >> 1 for a, b in f.items() if b > 1}
        self.inc /= self.decay
        inc = self.inc
        top = best = self.best
        for s in self.shadows:
            if s.access(key, fs[s.fi]):
                s.score += inc
            if s.score > top.score:
                top = s
        if top.score > best.score * self.margin:
            best = top
        if inc > 1e100:
            for s in self.shadows:
                s.score /= inc
            self.inc = 1.0
        store = self.store; extra = self.extra
        if best is not self.best:
            self.best = best
            self.switches += 1
            self.extra = extra = {k for k in store if k not in best.store}
        else:
            for k in best.ev:
                if k in store:
                    extra.add(k)
        for s in self.shadows:
            s.ev.clear()
        if key in store:
            if key in best.store:
                extra.discard(key)
            return True
        if key in best.store:
            store.add(key)
            if len(store) > self.cap:
                if self.vote and len(extra) > 1:
                    sh = self.shadows
                    v = min((sum(k in s.store for s in sh), k) for k, _ in zip(extra, range(self.vote)))[1]
                    extra.discard(v); store.discard(v)
                else:
                    store.discard(extra.pop())
        return False
