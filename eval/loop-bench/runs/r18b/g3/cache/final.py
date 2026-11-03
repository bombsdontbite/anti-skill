import heapq
from collections import OrderedDict, deque


class Freq:
    def __init__(self, reset):
        self.f = {}; self.ops = 0; self.reset = reset

    def inc(self, k):
        f = self.f
        f[k] = min(f.get(k, 0) + 1, 15)
        self.ops += 1
        if self.ops >= self.reset:
            self.ops //= 2
            self.f = {a: b >> 1 for a, b in f.items() if b > 1}


class TinyLFU:
    def __init__(self, cap, wcap, freq):
        self.cap = cap; self.wcap = wcap; self.freq = freq
        self.pcap = int((cap - wcap) * 0.8)
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.size = 0

    def has(self, k):
        return k in self.win or k in self.prob or k in self.prot

    def access(self, key):
        if key in self.win:
            self.win.move_to_end(key); return True, None
        if key in self.prot:
            self.prot.move_to_end(key); return True, None
        if key in self.prob:
            del self.prob[key]; self.prot[key] = True
            if len(self.prot) > self.pcap:
                k, _ = self.prot.popitem(last=False); self.prob[k] = True
            return True, None
        self.win[key] = True; self.size += 1
        if len(self.win) <= self.wcap:
            if self.size <= self.cap:
                return False, None
        cand, _ = self.win.popitem(last=False)
        if self.size <= self.cap:
            self.prob[cand] = True; return False, None
        self.size -= 1
        vq = self.prob if self.prob else self.prot
        victim = next(iter(vq))
        f = self.freq.f
        if f.get(cand, 0) > f.get(victim, 0):
            del vq[victim]; self.prob[cand] = True; return False, victim
        return False, cand


class ARC:
    def __init__(self, cap):
        self.c = cap; self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()

    def has(self, k):
        return k in self.t1 or k in self.t2

    def _replace(self, in_b2):
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        return k

    def access(self, key):
        c = self.c; ev = None
        if key in self.t1:
            del self.t1[key]; self.t2[key] = True; return True, None
        if key in self.t2:
            self.t2.move_to_end(key); return True, None
        if key in self.b1:
            self.p = min(c, self.p + max(1, len(self.b2) // len(self.b1)))
            ev = self._replace(False); del self.b1[key]; self.t2[key] = True
        elif key in self.b2:
            self.p = max(0, self.p - max(1, len(self.b1) // len(self.b2)))
            ev = self._replace(True); del self.b2[key]; self.t2[key] = True
        else:
            l1 = len(self.t1) + len(self.b1)
            tot = l1 + len(self.t2) + len(self.b2)
            if l1 == c:
                if len(self.t1) < c:
                    self.b1.popitem(last=False); ev = self._replace(False)
                else:
                    ev, _ = self.t1.popitem(last=False)
            elif l1 < c and tot >= c:
                if tot >= 2 * c:
                    self.b2.popitem(last=False)
                ev = self._replace(False)
            self.t1[key] = True
        return False, ev


class LIRS:
    def __init__(self, cap, hir_frac=0.01, ghost=2.0):
        self.cap = cap
        self.hcap = max(1, int(cap * hir_frac))
        self.lcap = cap - self.hcap
        self.S = OrderedDict()   # key -> True (LIR) / False (HIR)
        self.Q = OrderedDict()   # resident HIR
        self.lir = set()
        self.res = set()
        self.maxS = int(cap * (1 + ghost))

    def has(self, k):
        return k in self.res

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if k in self.lir:
                break
            del S[k]

    def _limit(self):
        S = self.S
        if len(S) > self.maxS:
            goal = self.maxS - self.cap // 4 - 1
            for k in list(S):
                if len(S) <= goal:
                    break
                if k not in self.lir and k not in self.res:
                    del S[k]

    def access(self, key):
        S, Q, lir = self.S, self.Q, self.lir
        if key in lir:
            first = next(iter(S))
            S.move_to_end(key)
            if first == key:
                self._prune()
            return True, None
        ev = None
        hit = key in self.res
        if hit:
            del Q[key]
        else:
            if len(lir) < self.lcap:
                lir.add(key); self.res.add(key)
                S[key] = True; S.move_to_end(key)
                return False, None
            if len(self.res) >= self.cap:
                ev, _ = Q.popitem(last=False); self.res.discard(ev)
            self.res.add(key)
        if key in S:
            S.move_to_end(key)
            lir.add(key)
            b = next(iter(S))
            lir.discard(b); del S[b]; Q[b] = True
            self._prune()
        else:
            S[key] = False; Q[key] = True
        self._limit()
        return hit, ev


class PNA:
    """Evicts the resident key predicted to be requested furthest in the future."""

    def __init__(self, cap, new_pen=1e9, w=0.5):
        self.cap = cap; self.new_pen = new_pen; self.w = w
        self.last = {}; self.iv = {}
        self.pred = {}          # resident key -> predicted next time
        self.hmax = []; self.hmin = []
        self.t = 0

    def has(self, k):
        return k in self.pred

    def _set(self, k, p):
        self.pred[k] = p
        heapq.heappush(self.hmax, (-p, k)); heapq.heappush(self.hmin, (p, k))

    def access(self, key):
        t = self.t = self.t + 1
        last = self.last.get(key)
        if last is None:
            p = t + self.new_pen
        else:
            d = t - last
            iv = self.iv.get(key)
            iv = d if iv is None else iv + self.w * (d - iv)
            self.iv[key] = iv
            p = t + iv
        self.last[key] = t
        pred = self.pred
        if key in pred:
            self._set(key, p); return True, None
        ev = None
        if len(pred) >= self.cap:
            hmin = self.hmin
            while hmin and hmin[0][0] < t:
                q, k = heapq.heappop(hmin)
                if pred.get(k) == q:
                    self._set(k, t + 2 * (t - self.last[k]))
            hmax = self.hmax
            while True:
                q, k = heapq.heappop(hmax)
                if pred.get(k) == -q:
                    break
            del pred[k]; ev = k
            if len(hmax) > 8 * self.cap:
                self.hmax = [(-v, k) for k, v in pred.items()]; heapq.heapify(self.hmax)
                self.hmin = [(v, k) for k, v in pred.items()]; heapq.heapify(self.hmin)
        self._set(key, p)
        return False, ev


class Cache:
    """Runs several policies on the same request stream and mirrors whichever has hit most lately.

    Experts: W-TinyLFU at six window sizes (small window suits loops and frequency, large suits
    recency) plus two whose counts age three times slower, LIRS, a predicted-next-request policy and ARC. The real cache only ever adds the
    requested key; on a miss it evicts a key the leader no longer holds, so it converges to the
    leader's contents after a switch.
    """

    def __init__(self, capacity, fracs=(0.01, 0.05, 0.15, 0.3, 0.5, 0.8),
                 slow_fracs=(0.01, 0.1), sample=10, slow_sample=30, horizon=15, margin=0.015):
        self.cap = capacity
        self.freqs = [Freq(capacity * sample), Freq(capacity * slow_sample)]
        ex = [TinyLFU(capacity, max(1, min(capacity - 1, int(capacity * x))), self.freqs[0])
              for x in fracs]
        ex += [TinyLFU(capacity, max(1, min(capacity - 1, int(capacity * x))), self.freqs[1])
               for x in slow_fracs]
        ex += [LIRS(capacity, 0.01), PNA(capacity), ARC(capacity)]
        self.experts = ex
        self.scores = [0.0] * len(ex)
        self.alpha = 1.0 / (capacity * horizon)
        self.margin = margin
        self.lead = 0
        self.every = max(1, capacity // 4); self.t = 0
        self.extra = deque()
        self.store = set()

    def access(self, key):
        for f in self.freqs:
            f.inc(key)
        a = self.alpha; sc = self.scores; lead = self.lead
        for i, e in enumerate(self.experts):
            h, ev = e.access(key)
            sc[i] += a * (h - sc[i])
            if i == lead and ev is not None:
                self.extra.append(ev)
        self.t += 1
        if self.t % self.every == 0:
            best = max(range(len(sc)), key=lambda i: sc[i])
            if sc[best] > sc[lead] + self.margin:
                self.lead = lead = best
                L = self.experts[lead]
                self.extra = deque(k for k in self.store if not L.has(k))
        st = self.store
        if key in st:
            return True
        if len(st) >= self.cap:
            L = self.experts[lead]
            ex = self.extra
            while True:
                if not ex:
                    k = next(iter(st))
                    break
                k = ex.popleft()
                if k in st and not L.has(k):
                    break
            st.discard(k)
        st.add(key)
        return False
