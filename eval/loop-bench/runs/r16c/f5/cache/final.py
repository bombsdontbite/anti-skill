import math
from collections import OrderedDict, deque


class LRU:
    def __init__(self, cap):
        self.cap = cap; self.store = OrderedDict(); self.ev = []

    def access(self, key):
        s = self.store
        if key in s:
            s.move_to_end(key); return True
        if len(s) >= self.cap:
            k, _ = s.popitem(last=False); self.ev.append(k)
        s[key] = True
        return False


class LIRS:
    def __init__(self, cap, hir=0.01, sb=3):
        self.cap = cap; self.sb = sb
        self.lcap = cap - max(1, int(cap * hir))
        self.S = OrderedDict(); self.Q = OrderedDict(); self.lir = set()
        self.store = set(); self.ev = []

    def _prune(self):
        S, lir = self.S, self.lir
        while S:
            k = next(iter(S))
            if k in lir:
                break
            del S[k]

    def _demote(self):
        S, lir = self.S, self.lir
        k, _ = S.popitem(last=False); lir.discard(k); self.Q[k] = True
        self._prune()

    def access(self, key):
        S, Q, lir = self.S, self.Q, self.lir
        if key in lir:
            S.move_to_end(key); self._prune(); return True
        if key in Q:
            if key in S:
                del Q[key]; S.move_to_end(key); lir.add(key); self._demote()
            else:
                Q.move_to_end(key); S[key] = True
            return True
        if len(lir) < self.lcap:
            lir.add(key); S[key] = True; self.store.add(key); return False
        if len(self.store) >= self.cap:
            v, _ = Q.popitem(last=False); self.store.discard(v); self.ev.append(v)
        self.store.add(key)
        if key in S:
            S.move_to_end(key); lir.add(key); self._demote()
        else:
            S[key] = True; Q[key] = True
        if len(S) > self.sb * self.cap:
            for k in [k for k in S if k not in lir and k not in Q][:len(S) - (self.sb - 1) * self.cap]:
                del S[k]
        return False


class TinyLFU:
    def __init__(self, cap, wfrac=0.01, rs=10):
        self.cap = cap
        self.wcap = max(1, int(cap * wfrac)); self.mcap = cap - self.wcap
        self.pcap = int(self.mcap * 0.8)
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.store = set(); self.freq = {}; self.ops = 0; self.reset = rs * cap; self.ev = []

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
        self.win[key] = True; self.store.add(key)
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = True
            else:
                vq = self.prob if self.prob else self.prot
                victim = next(iter(vq))
                if f.get(cand, 0) > f.get(victim, 0):
                    del vq[victim]; self.store.discard(victim); self.ev.append(victim)
                    self.prob[cand] = True
                else:
                    self.store.discard(cand); self.ev.append(cand)
        return False


class Cache:
    """Weighted vote of several simulated policies."""

    def __init__(self, capacity, half=32.0, eta=1.0, m=48, thr=0.5):
        self.cap = capacity
        self.experts = [LIRS(capacity, 0.01, 6), LRU(capacity), TinyLFU(capacity, 0.01, 20)]
        self.score = [0.0] * len(self.experts)
        self.decay = 1.0 - 1.0 / (half * capacity)
        self.eta = eta * 100.0 / (half * capacity)
        self.w = [1.0 / len(self.experts)] * len(self.experts)
        self.m = m; self.thr = thr
        self.store = OrderedDict()
        self.cand = deque(maxlen=4 * capacity)
        self.n = 0

    def access(self, key):
        d = self.decay
        sc = self.score
        ex = self.experts
        for i, e in enumerate(ex):
            sc[i] = sc[i] * d + e.access(key)
            if e.ev:
                self.cand.extend(e.ev); e.ev.clear()
        self.n += 1
        if self.n >= 16:
            self.n = 0
            top = max(sc); eta = self.eta
            w = [math.exp(eta * (x - top)) for x in sc]
            t = sum(w)
            self.w = [x / t for x in w]
        s = self.store
        if key in s:
            s.move_to_end(key); return True
        w = self.w
        if sum(w[i] for i, e in enumerate(ex) if key in e.store) < self.thr:
            return False
        if len(s) >= self.cap:
            best = -1.0; v = None; seen = 0
            cand = self.cand
            for j in range(len(cand) - 1, -1, -1):
                k = cand[j]
                if k in s:
                    a = sum(w[i] for i, e in enumerate(ex) if k not in e.store)
                    if a > best:
                        best = a; v = k
                    seen += 1
                    if seen >= self.m:
                        break
            if v is None or best < 0.5:
                for k in s:
                    a = sum(w[i] for i, e in enumerate(ex) if k not in e.store)
                    if a > best:
                        best = a; v = k
                    if a >= 0.5:
                        break
            del s[v]
        s[key] = True
        return False
