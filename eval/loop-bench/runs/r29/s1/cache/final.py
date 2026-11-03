from collections import OrderedDict, deque

class ARC:
    def __init__(self, capacity):
        self.c = capacity; self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict(); self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = set()
    def _replace(self, inb2):
        if self.t1 and (len(self.t1) > self.p or (inb2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        self.store.discard(k)
    def access(self, x):
        c = self.c
        if x in self.t1:
            del self.t1[x]; self.t2[x] = True; return True
        if x in self.t2:
            self.t2.move_to_end(x); return True
        if x in self.b1:
            self.p = min(c, self.p + max(len(self.b2) // max(len(self.b1),1), 1))
            self._replace(False); del self.b1[x]; self.t2[x] = True; self.store.add(x); return False
        if x in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // max(len(self.b2),1), 1))
            self._replace(True); del self.b2[x]; self.t2[x] = True; self.store.add(x); return False
        l1 = len(self.t1) + len(self.b1)
        if l1 == c:
            if len(self.t1) < c:
                self.b1.popitem(last=False); self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False); self.store.discard(k)
        else:
            tot = l1 + len(self.t2) + len(self.b2)
            if tot >= c:
                if tot == 2 * c: self.b2.popitem(last=False)
                self._replace(False)
        self.t1[x] = True; self.store.add(x); return False

class S3:
    """S3-FIFO."""
    def __init__(self, capacity):
        self.c = capacity; self.sc = max(1, capacity // 10)
        self.S = deque(); self.M = deque(); self.G = {}; self.gq = deque()
        self.freq = {}; self.store = set(); self.ms = 0
    def access(self, k):
        if k in self.store:
            if self.freq[k] < 3: self.freq[k] += 1
            return True
        while len(self.store) >= self.c: self._evict()
        if k in self.G:
            del self.G[k]; self.M.append(k); self.ms += 1
        else:
            self.S.append(k)
        self.freq[k] = 0; self.store.add(k); return False
    def _evict(self):
        if len(self.S) >= self.sc or not self.M:
            k = self.S.popleft()
            if self.freq[k] > 0:
                self.M.append(k); self.ms += 1; self.freq[k] = 0
                if self.ms > self.c - self.sc: self._evm()
            else:
                self.store.discard(k); del self.freq[k]
                self.G[k] = 1; self.gq.append(k)
                while len(self.gq) > self.c:
                    g = self.gq.popleft(); self.G.pop(g, None)
        else:
            self._evm()
    def _evm(self):
        while True:
            k = self.M.popleft()
            if self.freq[k] > 0:
                self.freq[k] -= 1; self.M.append(k)
            else:
                self.ms -= 1; self.store.discard(k); del self.freq[k]; return

class TLFU:
    """W-TinyLFU: small LRU window, SLRU main, frequency admission with aging."""
    def __init__(self, capacity, wfrac=0.01, rmul=10):
        self.c = capacity
        self.wc = max(1, int(capacity * wfrac))
        self.mc = capacity - self.wc
        self.pc = int(self.mc * 0.8)
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.freq = {}; self.ops = 0; self.reset = capacity * rmul
        self.store = set()
    def _inc(self, k):
        f = self.freq
        f[k] = f.get(k, 0) + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = {a: b >> 1 for a, b in f.items() if b > 1}
    def access(self, k):
        self._inc(k)
        if k in self.win:
            self.win.move_to_end(k); return True
        if k in self.prot:
            self.prot.move_to_end(k); return True
        if k in self.prob:
            del self.prob[k]; self.prot[k] = True
            if len(self.prot) > self.pc:
                d, _ = self.prot.popitem(last=False); self.prob[d] = True
            return True
        self.win[k] = True; self.store.add(k)
        if len(self.win) > self.wc:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mc:
                self.prob[cand] = True
            else:
                vq = self.prob if self.prob else self.prot
                victim = next(iter(vq))
                f = self.freq
                if f.get(cand, 0) > f.get(victim, 0):
                    del vq[victim]; self.store.discard(victim); self.prob[cand] = True
                else:
                    self.store.discard(cand)
        return False


class LIRS:
    def __init__(self, capacity):
        self.c = capacity; self.hc = max(1, capacity // 100); self.lc = capacity - self.hc
        self.S = OrderedDict(); self.Q = OrderedDict(); self.lir = set(); self.store = set()

    def _prune(self):
        S = self.S
        while S:
            b = next(iter(S))
            if b in self.lir:
                return
            del S[b]

    def _demote(self):
        b, _ = self.S.popitem(last=False)
        self.lir.discard(b); self.Q[b] = True
        self._prune()

    def access(self, x):
        S = self.S; Q = self.Q
        if x in self.lir:
            S[x] = True; S.move_to_end(x); self._prune(); return True
        if x in Q:
            if x in S:
                del Q[x]; S.move_to_end(x); self.lir.add(x); self._demote()
            else:
                S[x] = True; Q.move_to_end(x)
            return True
        if len(self.store) >= self.c:
            v, _ = Q.popitem(last=False); self.store.discard(v)
        self.store.add(x)
        if len(self.lir) < self.lc:
            self.lir.add(x); S[x] = True; S.move_to_end(x)
        elif x in S:
            S.move_to_end(x); self.lir.add(x); self._demote()
        else:
            S[x] = True; Q[x] = True
        if len(S) > 4 * self.c:
            st = self.store
            self.S = OrderedDict((k, True) for k in S if k in st)
            self._prune()
        return False


class Cache:
    """Follow the shadow policy with the best recent hit rate."""

    def __init__(self, capacity):
        self.c = capacity
        self.shadows = [ARC(capacity), S3(capacity), TLFU(capacity, 0.01), TLFU(capacity, 0.2), TLFU(capacity, 0.01, 100), TLFU(capacity, 0.01, 3), LIRS(capacity)]
        self.score = [0.0] * len(self.shadows)
        self.decay = 1.0 - 1.0 / (capacity * 10)
        self.lead = 0
        self.store = set()
        self.pend = []

    def access(self, k):
        sc = self.score; d = self.decay
        for i, s in enumerate(self.shadows):
            sc[i] = sc[i] * d + (1.0 if s.access(k) else 0.0)
        best = self.lead
        for i in range(len(sc)):
            if sc[i] > sc[best]:
                best = i
        if best != self.lead and sc[best] > sc[self.lead] * 1.02 + 0.5:
            self.lead = best
            self.pend = []
        st = self.store
        if k in st:
            return True
        if len(st) >= self.c:
            ls = self.shadows[self.lead].store
            pend = self.pend
            while True:
                if not pend:
                    pend.extend(v for v in st if v not in ls)
                v = pend.pop()
                if v in st and v not in ls:
                    break
            st.discard(v)
        st.add(k)
        return False
