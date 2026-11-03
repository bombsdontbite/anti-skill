from collections import OrderedDict, deque


class LRU:
    def __init__(self, c):
        self.c = c; self.store = OrderedDict(); self.ev = []

    def access(self, k):
        s = self.store
        if k in s:
            s.move_to_end(k); return True
        s[k] = True
        if len(s) > self.c:
            self.ev.append(s.popitem(last=False)[0])
        return False


class TinyLFU:
    def __init__(self, c, window=0.01, protected=0.8, sample=10):
        self.store = set(); self.ev = []
        self.wcap = max(1, int(c * window)); self.mcap = c - self.wcap
        self.pcap = int(self.mcap * protected)
        self.win, self.prob, self.prot = OrderedDict(), OrderedDict(), OrderedDict()
        self.freq = {}; self.ops = 0; self.reset = sample * c

    def access(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = f = {k: v >> 1 for k, v in f.items() if v > 1}
        if key in self.store:
            if key in self.win:
                self.win.move_to_end(key)
            elif key in self.prot:
                self.prot.move_to_end(key)
            else:
                del self.prob[key]; self.prot[key] = True
                if len(self.prot) > self.pcap:
                    self.prob[self.prot.popitem(last=False)[0]] = True
            return True
        self.store.add(key); self.win[key] = True
        if len(self.win) > self.wcap:
            cand = self.win.popitem(last=False)[0]
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = True
            else:
                q = self.prob if self.prob else self.prot
                victim = next(iter(q)) if q else None
                if q and f.get(cand, 0) > f.get(victim, 0):
                    del q[victim]; self.prob[cand] = True; out = victim
                else:
                    out = cand
                self.store.discard(out); self.ev.append(out)
        return False


class S3FIFO:
    def __init__(self, c, small=0.1):
        self.c = c; self.scap = max(1, int(c * small))
        self.S, self.M, self.gq = deque(), deque(), deque()
        self.G = {}; self.store = {}; self.ev = []

    def _out(self, k):
        del self.store[k]; self.ev.append(k)

    def _evict(self):
        f = self.store
        if len(self.S) >= self.scap or not self.M:
            while self.S:
                k = self.S.popleft()
                if f[k] > 0:
                    f[k] = 0; self.M.append(k)
                else:
                    self._out(k); self.G[k] = True; self.gq.append(k)
                    while len(self.G) > self.c:
                        self.G.pop(self.gq.popleft(), None)
                    return
        while self.M:
            k = self.M.popleft()
            if f[k] > 0:
                f[k] -= 1; self.M.append(k)
            else:
                self._out(k); return

    def access(self, k):
        f = self.store
        if k in f:
            if f[k] < 3: f[k] += 1
            return True
        if len(f) >= self.c:
            self._evict()
        f[k] = 0
        if k in self.G:
            del self.G[k]; self.M.append(k)
        else:
            self.S.append(k)
        return False


class LIRS:
    def __init__(self, c, hir=0.01):
        self.c = c; self.hcap = max(1, int(c * hir)); self.lcap = c - self.hcap
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
        S = self.S
        k = next(iter(S))
        del S[k]; self.lir.discard(k); self.Q[k] = True
        self._prune()

    def access(self, x):
        S, Q, lir, st = self.S, self.Q, self.lir, self.store
        if x in lir:
            bottom = next(iter(S)) == x
            S.move_to_end(x)
            if bottom:
                self._prune()
            return True
        if x in st:
            if x in S:
                S.move_to_end(x); del Q[x]; lir.add(x); self._demote()
            else:
                S[x] = True; Q.move_to_end(x)
            return True
        if len(lir) < self.lcap:
            S[x] = True; S.move_to_end(x); lir.add(x); st.add(x)
            return False
        if len(st) >= self.c:
            v = Q.popitem(last=False)[0]; st.discard(v); self.ev.append(v)
        st.add(x)
        if x in S:
            S.move_to_end(x); lir.add(x); self._demote()
        else:
            S[x] = True; Q[x] = True
        if len(S) > 4 * self.c:
            for k in list(S)[:self.c]:
                if k not in st:
                    del S[k]
            self._prune()
        return False


class Cache:
    """Shadow-simulates several policies and converges on the recent leader."""

    def __init__(self, capacity, half=6, margin=1.02, hir=0.01, add=0.1):
        self.c = capacity
        self.experts = [TinyLFU(capacity, sample=100), LRU(capacity), S3FIFO(capacity), LIRS(capacity, hir)]
        self.score = [0.0] * len(self.experts)
        self.decay = 1 - 1 / (half * capacity)
        self.margin = margin
        self.add = 0.5 + add * capacity
        self.lead = 0
        self.store = set()
        self.diff = OrderedDict()

    def access(self, key):
        d = self.decay; sc = self.score; ex = self.experts
        for i, e in enumerate(ex):
            sc[i] = sc[i] * d + e.access(key)
        best = max(range(len(ex)), key=lambda i: sc[i])
        if sc[best] > sc[self.lead] * self.margin + self.add:
            self.lead = best
            ls = ex[best].store
            self.diff = OrderedDict((k, True) for k in self.store if k not in ls)
        L = ex[self.lead]
        for v in L.ev:
            if v in self.store:
                self.diff[v] = True
        for e in ex:
            e.ev.clear()
        if key in L.store:
            self.diff.pop(key, None)
        s = self.store
        if key in s:
            return True
        if key not in L.store:
            return False
        s.add(key)
        if len(s) > self.c:
            if self.diff:
                v = self.diff.popitem(last=False)[0]
            else:
                v = next(iter(s - {key}))
            s.discard(v)
        return False
