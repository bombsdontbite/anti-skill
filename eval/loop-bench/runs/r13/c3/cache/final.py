from collections import OrderedDict, deque


class Freq:
    def __init__(self, capacity, mult):
        self.f = {}
        self.n = 0
        self.reset = mult * capacity

    def add(self, key):
        f = self.f
        f[key] = f.get(key, 0) + 1
        self.n += 1
        if self.n >= self.reset:
            self.n = 0
            self.f = {k: v >> 1 for k, v in f.items() if v > 1}


class LIRS:
    def __init__(self, capacity, frac, adm, freq, ghost_mult=3):
        self.c = capacity
        self.h = max(1, int(capacity * frac))
        self.adm = adm
        self.freq = freq
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.lir = set()
        self.store = set()
        self.log = deque()
        self.ghost_max = ghost_mult * capacity

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
        self.lir.discard(k); del S[k]; self.Q[k] = True
        self._prune()

    def _trim(self):
        S = self.S
        if len(S) > self.ghost_max + self.c:
            for k in list(S):
                if len(S) <= self.ghost_max:
                    break
                if k not in self.store:
                    del S[k]

    def access(self, key):
        S, Q, lir, store = self.S, self.Q, self.lir, self.store
        if key in lir:
            first = next(iter(S))
            S.move_to_end(key)
            if first == key:
                self._prune()
            return True
        if key in store:
            if key in S:
                lir.add(key); del Q[key]; S.move_to_end(key)
                self._demote()
            else:
                S[key] = True; Q.move_to_end(key)
            return True
        if len(store) >= self.c:
            if self.adm:
                f = self.freq.f
                if f.get(key, 0) <= f.get(next(iter(Q)), 0):
                    if key in S:
                        S.move_to_end(key)
                    else:
                        S[key] = True
                    self._trim()
                    return False
            k, _ = Q.popitem(last=False)
            store.discard(k); self.log.append(k)
        store.add(key)
        if len(lir) < self.c - self.h:
            lir.add(key); S[key] = True; S.move_to_end(key)
        elif key in S:
            lir.add(key); S.move_to_end(key)
            self._demote()
        else:
            S[key] = True; Q[key] = True
        self._trim()
        return False


class ARC:
    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = set()
        self.log = deque()

    def _replace(self, in_b2):
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        self.store.discard(k); self.log.append(k)

    def access(self, key):
        c = self.c
        if key in self.t1:
            del self.t1[key]; self.t2[key] = True; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p = min(c, self.p + max(len(self.b2) // len(self.b1), 1))
            del self.b1[key]; self._replace(False); self.t2[key] = True
        elif key in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // len(self.b2), 1))
            del self.b2[key]; self._replace(True); self.t2[key] = True
        else:
            l1 = len(self.t1) + len(self.b1)
            if l1 == c:
                if len(self.t1) < c:
                    self.b1.popitem(last=False); self._replace(False)
                else:
                    k, _ = self.t1.popitem(last=False)
                    self.store.discard(k); self.log.append(k)
            elif l1 < c:
                tot = l1 + len(self.t2) + len(self.b2)
                if tot >= c:
                    if tot == 2 * c:
                        self.b2.popitem(last=False)
                    self._replace(False)
            self.t1[key] = True
        self.store.add(key)
        return False


class TinyLFU:
    def __init__(self, capacity, freq, win=0.01, prot=0.8):
        self.c = capacity
        self.wc = max(1, int(capacity * win))
        self.mc = capacity - self.wc
        self.pc = int(self.mc * prot)
        self.W = OrderedDict(); self.P = OrderedDict(); self.R = OrderedDict()
        self.store = set()
        self.log = deque()
        self.freq = freq

    def access(self, key):
        if key in self.W:
            self.W.move_to_end(key); return True
        if key in self.P:
            self.P.move_to_end(key); return True
        if key in self.R:
            del self.R[key]; self.P[key] = True
            if len(self.P) > self.pc:
                k, _ = self.P.popitem(last=False); self.R[k] = True
            return True
        self.store.add(key)
        self.W[key] = True
        if len(self.W) > self.wc:
            cand, _ = self.W.popitem(last=False)
            if len(self.R) + len(self.P) < self.mc:
                self.R[cand] = True
            else:
                f = self.freq.f
                vic = next(iter(self.R)) if self.R else next(iter(self.P))
                if f.get(cand, 0) > f.get(vic, 0):
                    if vic in self.R: del self.R[vic]
                    else: del self.P[vic]
                    self.store.discard(vic); self.log.append(vic); self.R[cand] = True
                else:
                    self.store.discard(cand); self.log.append(cand)
        return False


class S3FIFO:
    def __init__(self, capacity, small_frac=0.1):
        self.c = capacity
        self.sc = max(1, int(capacity * small_frac))
        self.S = deque(); self.M = deque()
        self.G = {}; self.gq = deque()
        self.f = {}
        self.store = self.f
        self.log = deque()

    def _evictM(self):
        M, f = self.M, self.f
        while True:
            k = M.popleft()
            if f[k] > 0:
                f[k] -= 1; M.append(k)
            else:
                del f[k]; self.log.append(k); return

    def _evict(self):
        S, f = self.S, self.f
        if len(S) >= self.sc or not self.M:
            while S:
                k = S.popleft()
                if f[k] > 0:
                    f[k] = 0; self.M.append(k)
                    if len(self.M) > self.c - self.sc and len(self.M) + len(S) >= self.c:
                        self._evictM(); return
                    if len(S) + len(self.M) < self.c:
                        return
                else:
                    del f[k]; self.log.append(k)
                    self.G[k] = True; self.gq.append(k)
                    if len(self.gq) > self.c:
                        g = self.gq.popleft(); self.G.pop(g, None)
                    return
        self._evictM()

    def access(self, key):
        f = self.f
        if key in f:
            if f[key] < 3: f[key] += 1
            return True
        while len(f) >= self.c:
            self._evict()
        f[key] = 0
        if key in self.G:
            del self.G[key]; self.M.append(key)
        else:
            self.S.append(key)
        return False


class Cache:
    """Runs several policies as shadows; the real cache follows the one with most recent hits."""

    def __init__(self, capacity, decay_mult=32, freq_mult=30, margin=1.02):
        self.margin = margin
        self.cur = 0
        self.c = capacity
        fr = self.fr = Freq(capacity, freq_mult)
        self.shadows = [
            LIRS(capacity, 0.01, False, fr), LIRS(capacity, 0.1, False, fr),
            LIRS(capacity, 0.3, False, fr), LIRS(capacity, 0.6, False, fr),
            LIRS(capacity, 0.01, True, fr), LIRS(capacity, 0.1, True, fr),
            ARC(capacity), TinyLFU(capacity, fr), S3FIFO(capacity),
        ]
        self.score = [0.0] * len(self.shadows)
        self.d = 1.0 - 1.0 / (decay_mult * capacity)
        self.store = set()
        self.loglim = 4 * capacity

    def _victim(self, b):
        st, bs, log = self.store, b.store, b.log
        while log:
            k = log.popleft()
            if k in st and k not in bs:
                return k
        for k in st:
            if k not in bs:
                return k
        return next(iter(st))

    def access(self, key):
        self.fr.add(key)
        sc, d = self.score, self.d
        best = 0
        for i, s in enumerate(self.shadows):
            v = sc[i] * d
            if s.access(key):
                v += 1.0
            sc[i] = v
            if len(s.log) > self.loglim:
                s.log.popleft()
            if v > sc[best]:
                best = i
        if sc[best] > sc[self.cur] * self.margin + 1.0:
            self.cur = best
        best = self.cur
        st = self.store
        if key in st:
            return True
        b = self.shadows[best]
        if key in b.store:
            if len(st) >= self.c:
                st.discard(self._victim(b))
            st.add(key)
        return False
