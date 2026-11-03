from collections import OrderedDict, deque
PROT=0.8; RESET=10; FRACS=(0.01, 0.05, 0.2, 0.5, 0.8, 0.99); HIRS=(0.01, 0.1); OTHERS=('arc', 's3'); HALF=10.0; MARGIN=0.02; FAST=(0.01, 0.2); FRESET=1000000


class TinyLFU:
    def __init__(self, cap, wcap):
        self.cap = cap; self.wcap = wcap; self.fast = None
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.store = {}; self.ev = deque(maxlen=cap)

    def access(self, k, f):
        if self.fast: f = self.fast[0]
        win = self.win; prob = self.prob; prot = self.prot
        if k in win: win.move_to_end(k); return True
        if k in prot: prot.move_to_end(k); return True
        cap = self.cap; wcap = self.wcap
        if k in prob:
            del prob[k]; prot[k] = 1
            pcap = int((cap - wcap) * PROT)
            while len(prot) > pcap:
                d, _ = prot.popitem(last=False); prob[d] = 1
            return True
        store = self.store
        win[k] = 1; store[k] = 1
        if len(win) > wcap:
            c, _ = win.popitem(last=False)
            if len(prob) + len(prot) < cap - wcap:
                prob[c] = 1
            else:
                vq = prob if prob else prot
                v = next(iter(vq))
                if f.get(c, 0) > f.get(v, 0):
                    del vq[v]; del store[v]; prob[c] = 1; self.ev.append(v)
                else:
                    del store[c]; self.ev.append(c)
        return False


class LIRS:
    def __init__(self, cap, hcap):
        self.cap = cap; self.lcap = cap - hcap
        self.S = OrderedDict(); self.Q = OrderedDict(); self.NR = OrderedDict()
        self.lir = set(); self.store = {}; self.ev = deque(maxlen=cap)

    def _prune(self):
        S = self.S; lir = self.lir
        while S:
            b = next(iter(S))
            if b in lir: return
            del S[b]; self.NR.pop(b, None)

    def _demote(self):
        S = self.S
        b, _ = S.popitem(last=False)
        self.lir.discard(b); self.Q[b] = 1
        self._prune()

    def access(self, k, f):
        S = self.S; Q = self.Q; lir = self.lir; store = self.store
        if k in lir:
            first = next(iter(S)) == k
            S.move_to_end(k)
            if first: self._prune()
            return True
        hit = k in store
        if not hit:
            if len(lir) < self.lcap:
                lir.add(k); S[k] = 1; store[k] = 1
                return False
            if len(store) >= self.cap:
                v, _ = Q.popitem(last=False); del store[v]; self.ev.append(v)
                if v in S:
                    self.NR[v] = 1
                    if len(self.NR) > 2 * self.cap:
                        o, _ = self.NR.popitem(last=False); del S[o]
            store[k] = 1
        if k in S:
            S.move_to_end(k); self.NR.pop(k, None); Q.pop(k, None); lir.add(k)
            self._demote()
        else:
            S[k] = 1; Q[k] = 1; Q.move_to_end(k)
        return hit


class ARC:
    def __init__(self, cap, _):
        self.c = cap; self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict(); self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = {}; self.ev = deque(maxlen=cap)

    def _rep(self, inb2):
        if self.t1 and (len(self.t1) > self.p or (inb2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = 1
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = 1
        del self.store[k]; self.ev.append(k)

    def access(self, x, f):
        c = self.c; t1 = self.t1; t2 = self.t2; b1 = self.b1; b2 = self.b2
        if x in t1: del t1[x]; t2[x] = 1; return True
        if x in t2: t2.move_to_end(x); return True
        if x in b1:
            self.p = min(c, self.p + max(len(b2) // len(b1), 1)); self._rep(False); del b1[x]; t2[x] = 1
        elif x in b2:
            self.p = max(0, self.p - max(len(b1) // len(b2), 1)); self._rep(True); del b2[x]; t2[x] = 1
        else:
            l1 = len(t1) + len(b1)
            if l1 == c:
                if len(t1) < c: b1.popitem(last=False); self._rep(False)
                else:
                    k, _ = t1.popitem(last=False); del self.store[k]; self.ev.append(k)
            elif l1 < c and l1 + len(t2) + len(b2) >= c:
                if l1 + len(t2) + len(b2) == 2 * c: b2.popitem(last=False)
                self._rep(False)
            t1[x] = 1
        self.store[x] = 1
        return False


class S3FIFO:
    def __init__(self, cap, _):
        self.cap = cap; self.scap = max(1, cap // 10); self.mcap = cap - self.scap
        self.S = deque(); self.M = deque(); self.G = OrderedDict(); self.store = {}; self.ev = deque(maxlen=cap)

    def _evict(self, k):
        del self.store[k]; self.ev.append(k)

    def access(self, k, f):
        st = self.store
        if k in st:
            if st[k] < 3: st[k] += 1
            return True
        while len(st) >= self.cap:
            if len(self.S) >= self.scap or not self.M:
                while self.S:
                    x = self.S.popleft()
                    if st[x] > 0:
                        self.M.append(x); st[x] = 0
                        if len(self.M) > self.mcap: self._evm()
                    else:
                        self._evict(x); self.G[x] = 1
                        if len(self.G) > self.mcap: self.G.popitem(last=False)
                        break
            else:
                self._evm()
        if k in self.G:
            del self.G[k]; self.M.append(k)
        else:
            self.S.append(k)
        st[k] = 0
        return False

    def _evm(self):
        M = self.M; st = self.store
        while True:
            x = M.popleft()
            if st[x] > 0: st[x] -= 1; M.append(x)
            else: self._evict(x); return


KINDS = {'arc': ARC, 's3': S3FIFO}


class Cache:
    def __init__(self, capacity):
        self.cap = capacity
        ws = sorted(set(min(capacity - 1, max(1, int(round(capacity * x)))) for x in FRACS))
        hs = sorted(set(min(capacity - 1, max(1, int(round(capacity * x)))) for x in HIRS))
        self.sims = [TinyLFU(capacity, w) for w in ws] + [LIRS(capacity, h) for h in hs] + [KINDS[o](capacity, 0) for o in OTHERS]
        self.f2 = [{}]; self.ops2 = 0
        for x in FAST:
            t = TinyLFU(capacity, max(1, int(capacity * x))); t.fast = self.f2; self.sims.append(t)
        self.score = [0.0] * len(self.sims)
        self.decay = 1.0 - 1.0 / (HALF * capacity)
        self.cur = 0
        self.store = {}
        self.freq = {}; self.ops = 0; self.reset = RESET * capacity

    def access(self, k):
        f = self.freq; v = f.get(k, 0)
        if v < 15: f[k] = v + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0; self.freq = f = {a: b >> 1 for a, b in f.items() if b > 1}
        if FAST:
            g = self.f2[0]; v = g.get(k, 0)
            if v < 255: g[k] = v + 1
            self.ops2 += 1
            if self.ops2 >= FRESET * self.cap:
                self.ops2 = 0; self.f2[0] = {a: b >> 1 for a, b in g.items() if b > 1}
        d = self.decay; sc = self.score; best = 0
        for i, s in enumerate(self.sims):
            sc[i] = sc[i] * d + (1.0 if s.access(k, f) else 0.0)
            if sc[i] > sc[best]: best = i
        cur = self.cur
        if best != cur and sc[best] > sc[cur] * (1.0 + MARGIN):
            self.cur = cur = best
        store = self.store
        if k in store:
            return True
        store[k] = 1
        if len(store) > self.cap:
            lead = self.sims[cur]; ls = lead.store; ev = lead.ev
            while ev:
                x = ev.pop()
                if x in store and x not in ls:
                    del store[x]; return False
            for x in store:
                if x not in ls:
                    del store[x]; return False
        return False
