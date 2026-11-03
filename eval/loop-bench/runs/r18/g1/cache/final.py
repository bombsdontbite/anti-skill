from collections import OrderedDict, deque
import heapq


class LRU:
    def __init__(self, c):
        self.c = c; self.store = OrderedDict(); self.ev = None

    def access(self, key):
        s = self.store; self.ev = None
        if key in s:
            s.move_to_end(key); return True
        if len(s) >= self.c:
            self.ev = s.popitem(last=False)[0]
        s[key] = True
        return False


class ARC:
    def __init__(self, c):
        self.c = c; self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = set(); self.ev = None

    def _replace(self, in_b2):
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        self.store.discard(k); self.ev = k

    def access(self, key):
        c = self.c; self.ev = None
        if key in self.t1:
            del self.t1[key]; self.t2[key] = True; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p = min(c, self.p + max(len(self.b2) // max(len(self.b1), 1), 1))
            self._replace(False); del self.b1[key]; self.t2[key] = True; self.store.add(key); return False
        if key in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // max(len(self.b2), 1), 1))
            self._replace(True); del self.b2[key]; self.t2[key] = True; self.store.add(key); return False
        l1 = len(self.t1) + len(self.b1)
        if l1 == c:
            if len(self.t1) < c:
                self.b1.popitem(last=False); self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False); self.store.discard(k); self.ev = k
        else:
            tot = l1 + len(self.t2) + len(self.b2)
            if tot >= c:
                if tot == 2 * c and self.b2:
                    self.b2.popitem(last=False)
                if len(self.t1) + len(self.t2) >= c:
                    self._replace(False)
        self.t1[key] = True; self.store.add(key)
        return False


class S3FIFO:
    def __init__(self, c):
        self.c = c; self.sc = max(1, c // 10)
        self.S = deque(); self.M = deque(); self.G = {}; self.gq = deque()
        self.store = {}; self.ns = 0; self.ev = None

    def _evict(self):
        S, M, f = self.S, self.M, self.store
        if self.ns >= self.sc or not M:
            while S:
                k = S.popleft(); self.ns -= 1
                if f[k] > 0:
                    f[k] = 0; M.append(k)
                else:
                    del f[k]; self.ev = k; self.G[k] = 1; self.gq.append(k)
                    while len(self.gq) > self.c:
                        self.G.pop(self.gq.popleft(), None)
                    return
        while M:
            k = M.popleft()
            if f[k] > 0:
                f[k] -= 1; M.append(k)
            else:
                del f[k]; self.ev = k; return

    def access(self, key):
        f = self.store; self.ev = None
        if key in f:
            if f[key] < 3: f[key] += 1
            return True
        if len(f) >= self.c:
            self._evict()
        if key in self.G:
            del self.G[key]; self.M.append(key)
        else:
            self.S.append(key); self.ns += 1
        f[key] = 0
        return False


class TLFU:
    """W-TinyLFU; counts are shared and updated by the caller."""

    def __init__(self, c, wfrac, freq, pfrac=0.8):
        self.c = c; self.wc = max(1, int(c * wfrac)); self.mc = c - self.wc
        self.pc = int(self.mc * pfrac); self.freq = freq
        self.W = OrderedDict(); self.P = OrderedDict(); self.R = OrderedDict()
        self.store = set(); self.ev = None

    def access(self, key):
        self.ev = None
        W, P, R = self.W, self.P, self.R
        if key in W:
            W.move_to_end(key); return True
        if key in P:
            P.move_to_end(key); return True
        if key in R:
            del R[key]; P[key] = True
            if len(P) > self.pc:
                k, _ = P.popitem(last=False); R[k] = True
            return True
        self.store.add(key); W[key] = True
        if len(W) > self.wc:
            cand, _ = W.popitem(last=False)
            if len(R) + len(P) < self.mc:
                R[cand] = True
            else:
                vq = R if R else P
                vic = next(iter(vq))
                cnt = self.freq.cnt
                if cnt.get(cand, 0) > cnt.get(vic, 0):
                    del vq[vic]; self.store.discard(vic); R[cand] = True; self.ev = vic
                else:
                    self.store.discard(cand); self.ev = cand
        return False


class LIRS:
    def __init__(self, c, hfrac=0.01):
        self.c = c; self.hc = max(1, int(c * hfrac)); self.lc = c - self.hc
        self.S = OrderedDict(); self.Q = OrderedDict(); self.NR = OrderedDict()
        self.lir = set(); self.store = set(); self.ev = None

    def _prune(self):
        S, lir, NR = self.S, self.lir, self.NR
        while S:
            k = next(iter(S))
            if k in lir:
                return
            del S[k]
            if k in NR:
                del NR[k]

    def _demote(self):
        S = self.S
        k = next(iter(S))
        del S[k]; self.lir.discard(k); self.Q[k] = True
        self._prune()

    def access(self, key):
        self.ev = None
        S, Q, lir = self.S, self.Q, self.lir
        if key in lir:
            first = next(iter(S)) == key
            S.move_to_end(key)
            if first:
                self._prune()
            return True
        if key in Q:
            if key in S:
                del Q[key]; S.move_to_end(key); lir.add(key); self._demote()
            else:
                S[key] = True; Q.move_to_end(key)
            return True
        store = self.store
        if len(lir) < self.lc and not Q:
            lir.add(key); store.add(key); S[key] = True; S.move_to_end(key)
            self.NR.pop(key, None)
            return False
        if len(store) >= self.c:
            v, _ = Q.popitem(last=False); store.discard(v); self.ev = v
            if v in S:
                self.NR[v] = True
                if len(self.NR) > 4 * self.c:
                    o, _ = self.NR.popitem(last=False); del S[o]
                    self._prune()
        store.add(key)
        if key in S:
            del self.NR[key]; S.move_to_end(key); lir.add(key); self._demote()
        else:
            S[key] = True; Q[key] = True
        return False


class MRU:
    def __init__(self, c):
        self.c = c; self.store = OrderedDict(); self.ev = None

    def access(self, key):
        s = self.store; self.ev = None
        if key in s:
            s.move_to_end(key); return True
        if len(s) >= self.c:
            self.ev = s.popitem()[0]
        s[key] = True
        return False


class PRED:
    """Evict the key whose predicted next access (last + EWMA gap) is farthest away."""

    def __init__(self, capacity, prior=30.0, alpha=0.3, overdue=1.2):
        self.ev = None
        self.c = capacity
        self.store = OrderedDict()
        self.last = {}; self.ival = {}; self.pred = {}
        self.h = []; self.t = 0
        self.prior = prior * capacity; self.a = alpha; self.od = overdue

    def access(self, key):
        self.t += 1; t = self.t; self.ev = None
        last = self.last; ival = self.ival
        if key in last:
            g = t - last[key]
            iv = ival.get(key)
            iv = g if iv is None else iv + self.a * (g - iv)
            ival[key] = iv
        else:
            iv = self.prior
        last[key] = t
        p = t + iv
        s = self.store
        if key in s:
            s.move_to_end(key); self.pred[key] = p
            heapq.heappush(self.h, (-p, key)); return True
        if len(s) >= self.c:
            o = next(iter(s))
            io = ival.get(o, self.prior)
            if t - last[o] > self.od * io:
                vic = o
            else:
                h = self.h; pred = self.pred
                while True:
                    np_, k = h[0]
                    if k in s and pred[k] == -np_:
                        break
                    heapq.heappop(h)
                if -np_ < p:
                    return False
                vic = k
            del s[vic]; del self.pred[vic]; self.ev = vic
        s[key] = True; self.pred[key] = p
        heapq.heappush(self.h, (-p, key))
        if len(self.h) > 8 * self.c:
            self.h = [(-q, k) for k, q in self.pred.items()]; heapq.heapify(self.h)
        if len(last) > 50 * self.c:
            cut = t - 20 * self.c
            self.last = {k: v for k, v in last.items() if v > cut or k in s}
            self.ival = {k: v for k, v in ival.items() if k in self.last}
        return False


class Freq:
    def __init__(self, c):
        self.cnt = {}; self.ops = 0; self.reset = 10 * c

    def add(self, key):
        cnt = self.cnt
        v = cnt.get(key, 0)
        if v < 15: cnt[key] = v + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.cnt = {a: b >> 1 for a, b in cnt.items() if b > 1}


class Cache:
    """Runs several policies in shadow and steers the real contents toward the recent best."""

    def __init__(self, capacity, decay=None, margin=1.02):
        c = self.c = capacity
        self.freq = Freq(c)
        self.experts = [LRU(c), ARC(c), S3FIFO(c), TLFU(c, 0.01, self.freq), TLFU(c, 0.2, self.freq), LIRS(c), PRED(c), PRED(c, overdue=1.06)]
        self.score = [0.0] * len(self.experts)
        self.decay = decay if decay is not None else 1.0 - 1.0 / (4 * c)
        self.margin = margin
        self.lead = 3
        self.store = set()
        self.extra = OrderedDict()
        self.tick = 0; self.every = max(1, c // 16)

    def _switch(self, i):
        self.lead = i
        ls = self.experts[i].store
        self.extra = OrderedDict((k, True) for k in self.store if k not in ls)

    def access(self, key):
        self.freq.add(key)
        hit = key in self.store
        d = self.decay; sc = self.score
        for i, e in enumerate(self.experts):
            sc[i] = sc[i] * d + e.access(key)
        L = self.experts[self.lead]
        extra = self.extra
        ev = L.ev
        if ev is not None and ev in self.store:
            extra[ev] = True
        if hit:
            if key in extra and key in L.store:
                del extra[key]
            return True
        self.tick += 1
        if self.tick >= self.every:
            self.tick = 0
            best = 0
            for i in range(1, len(sc)):
                if sc[i] > sc[best]:
                    best = i
            gap = sc[best] - sc[self.lead] - 2 * (sc[self.lead] + 1.0) ** 0.5
            if best != self.lead and gap > 0:
                bs = self.experts[best].store
                diff = sum(1 for k in self.store if k not in bs)
                if gap > 0.25 * diff:
                    self._switch(best); L = self.experts[best]; extra = self.extra
        if key in L.store:
            store = self.store
            if len(store) >= self.c:
                k, _ = extra.popitem(last=False)
                store.discard(k)
            store.add(key)
        return False
