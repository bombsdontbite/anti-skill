from collections import OrderedDict, deque
from heapq import heappush, heappop, heapify


"""Follow-the-leader ensemble: four policies run as shadows; the real cache evicts
the oldest key the currently best shadow (by recent hits) no longer holds."""


class LIRS:
    def __init__(self, cap, hir_frac, smax=3.0):
        self.cap = cap
        self.lcap = cap - max(1, int(cap * hir_frac))
        self.S = OrderedDict(); self.Q = OrderedDict()
        self.lir = set(); self.store = set(); self.nr = deque()
        self.maxS = int(smax * cap)

    def _prune(self):
        S, lir = self.S, self.lir
        while S:
            k = next(iter(S))
            if k in lir: break
            del S[k]

    def access(self, key, ev):
        S, Q, lir, store = self.S, self.Q, self.lir, self.store
        if key in lir:
            first = next(iter(S)) == key
            S.move_to_end(key)
            if first: self._prune()
            return True
        hit = key in store
        if hit:
            del Q[key]
        else:
            if len(store) >= self.cap:
                v = Q.popitem(last=False)[0]; store.discard(v); ev.append(v)
                if v in S: self.nr.append(v)
            store.add(key)
            if len(lir) < self.lcap and key not in S:
                lir.add(key); S[key] = 1; return False
        if key in S:
            S.move_to_end(key); lir.add(key)
            b = S.popitem(last=False)[0]; lir.discard(b); Q[b] = 1
            self._prune()
        else:
            S[key] = 1; Q[key] = 1
        if len(S) > self.maxS:
            nr = self.nr
            while len(S) > self.maxS and nr:
                k = nr.popleft()
                if k in S and k not in store: del S[k]
        return hit


class TLFU:
    def __init__(self, cap, wfrac=0.01, age=10):
        self.cap = cap
        self.wcap = max(1, int(cap * wfrac))
        self.mcap = cap - self.wcap
        self.pcap = int(self.mcap * 0.8)
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.freq = {}; self.n = 0; self.reset = age * cap
        self.store = set()

    def access(self, key, ev):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.n += 1
        if self.n >= self.reset:
            self.n = 0
            self.freq = f = {a: b >> 1 for a, b in f.items() if b > 1}
        if key in self.win:
            self.win.move_to_end(key); return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key] = 1
            if len(self.prot) > self.pcap:
                self.prob[self.prot.popitem(last=False)[0]] = 1
            return True
        self.store.add(key); self.win[key] = 1
        if len(self.win) > self.wcap:
            cand = self.win.popitem(last=False)[0]
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = 1
            else:
                q = self.prob if self.prob else self.prot
                victim = next(iter(q))
                if f.get(cand, 0) > f.get(victim, 0):
                    del q[victim]; self.store.discard(victim); ev.append(victim)
                    self.prob[cand] = 1
                else:
                    self.store.discard(cand); ev.append(cand)
        return False


class PREDX:
    def __init__(self, cap, unk=2.0, alpha=0.5):
        self.cap = cap; self.unk = unk * cap; self.a = alpha
        self.last = {}; self.iv = {}; self.t = 0
        self.store = OrderedDict(); self.h = []; self.hq = deque()

    def access(self, key, ev):
        t = self.t = self.t + 1
        last, iv = self.last, self.iv
        l = last.get(key)
        if l is not None:
            d = t - l; o = iv.get(key)
            v = iv[key] = d if o is None else o + self.a * (d - o)
        else:
            v = self.unk
            self.hq.append(key)
            if len(self.hq) > 8 * self.cap:
                old = self.hq.popleft()
                if old in self.store: self.hq.append(old)
                else: last.pop(old, None); iv.pop(old, None)
        last[key] = t; v0 = v
        s = self.store; h = self.h
        if key in s:
            heappush(h, (-(t + v), t, key))
            s.move_to_end(key)
            if len(h) > 4 * self.cap: self._clean()
            return True
        if len(s) >= self.cap:
            while True:
                nv, lt, k = h[0]
                if last.get(k) == lt and k in s: break
                heappop(h)
            ok = next(iter(s))
            if -nv - t >= t - last[ok]:
                heappop(h); v = k
            else:
                v = ok
            del s[v]; ev.append(v)
        s[key] = 1
        heappush(h, (-(t + v0), t, key))
        return False

    def _clean(self):
        s, last = self.store, self.last
        self.h = [x for x in self.h if x[2] in s and last.get(x[2]) == x[1]]
        heapify(self.h)


def experts(c):
    return [LIRS(c, 0.01, 6.0), TLFU(c, 0.01, 100), PREDX(c, unk=0.5), PREDX(c, unk=8)]


class Cache:
    def __init__(self, capacity, decay=15, hyst=1.02):
        self.cap = capacity
        self.experts = experts(capacity)
        self.D = [OrderedDict() for _ in self.experts]
        self.sc = [0.0] * len(self.experts)
        self.lead = 0
        self.decay = 1.0 - 1.0 / (decay * capacity)
        self.hyst = hyst
        self.store = set()

    def access(self, key):
        real = self.store
        sc, d = self.sc, self.decay
        best = -1.0
        for i, e in enumerate(self.experts):
            ev = []
            h = e.access(key, ev)
            sc[i] = sc[i] * d + h
            De = self.D[i]
            De.pop(key, None)
            for v in ev:
                if v in real: De[v] = 1
            if sc[i] > best + 1e-9:
                best = sc[i]; lead = i
        cur = self.lead
        if sc[lead] > sc[cur] * self.hyst + 1.0:
            self.lead = cur = lead
        lead = cur
        if key in real:
            return True
        if len(real) >= self.cap:
            De = self.D[lead]
            v = De.popitem(last=False)[0]
            real.discard(v)
            for Dj in self.D:
                Dj.pop(v, None)
        real.add(key)
        return False
