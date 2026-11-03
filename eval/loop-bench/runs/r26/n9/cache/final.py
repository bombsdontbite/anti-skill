import heapq
from collections import OrderedDict, deque


class _S(set):
    def discard(self, k):
        if k in self:
            set.remove(self, k)
            self.ev.append(k)



class _Lirs:
    """LIRS with 1% HIR resident portion and bounded non-resident history."""

    def __init__(self, capacity, hir=0.01, hist=2.0):
        self.cap = capacity
        self.hcap = max(1, int(capacity * hir))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict()  # key -> True (LIR) / False (HIR)
        self.Q = OrderedDict()  # resident HIR
        self.lir = set()
        self.maxS = int(capacity * (1 + hist))
        self.store = _S(); self.store.ev = []

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if k in self.lir:
                break
            del S[k]

    def access(self, key):
        S, Q, lir = self.S, self.Q, self.lir
        if key in lir:
            S.move_to_end(key); self._prune(); return True
        hit = key in self.store
        if hit:
            if key in S:
                del Q[key]; lir.add(key); S.move_to_end(key)
                k = next(iter(S)); lir.discard(k); del S[k]; Q[k] = True
                self._prune()
            else:
                S[key] = False; Q.move_to_end(key)
            self._trim()
            return True
        # miss
        if len(lir) < self.lcap:
            lir.add(key); S[key] = True; S.move_to_end(key); self.store.add(key); return False
        if len(self.store) >= self.cap:
            v, _ = Q.popitem(last=False); self.store.discard(v)
        self.store.add(key)
        if key in S:
            lir.add(key); S.move_to_end(key)
            k = next(iter(S)); lir.discard(k); del S[k]; Q[k] = True
            self._prune()
        else:
            S[key] = False; Q[key] = True
        self._trim()
        return False

    def _trim(self):
        S = self.S
        if len(S) > self.maxS + self.cap:
            for k in list(S):
                if len(S) <= self.maxS:
                    break
                if k not in self.lir and k not in self.store:
                    del S[k]



class _Arc:
    """ARC."""

    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = _S(); self.store.ev = []

    def _replace(self, in_b2):
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        self.store.discard(k)

    def access(self, key):
        c = self.c
        if key in self.t1:
            del self.t1[key]; self.t2[key] = True; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p = min(c, self.p + max(len(self.b2) // len(self.b1), 1))
            self._replace(False); del self.b1[key]; self.t2[key] = True; self.store.add(key); return False
        if key in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // len(self.b2), 1))
            self._replace(True); del self.b2[key]; self.t2[key] = True; self.store.add(key); return False
        l1 = len(self.t1) + len(self.b1)
        if l1 == c:
            if len(self.t1) < c:
                self.b1.popitem(last=False); self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False); self.store.discard(k)
        else:
            tot = l1 + len(self.t2) + len(self.b2)
            if tot >= c:
                if tot == 2 * c and self.b2:
                    self.b2.popitem(last=False)
                if len(self.t1) + len(self.t2) >= c:
                    self._replace(False)
        self.t1[key] = True; self.store.add(key)
        return False



class _Tlfu:
    """W-TinyLFU: 1% LRU window, SLRU main, frequency-sketch admission with aging."""

    def __init__(self, capacity, window=0.01, prot=0.8, reset=10, cmax=15):
        self.cap = capacity
        self.wcap = max(1, int(capacity * window))
        self.mcap = capacity - self.wcap
        self.pcap = int(self.mcap * prot)
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.freq = {}
        self.ops = 0
        self.reset = capacity * reset
        self.cmax = cmax
        self.store = _S(); self.store.ev = []

    def _inc(self, k):
        f = self.freq
        v = f.get(k, 0)
        if v < self.cmax:
            f[k] = v + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops //= 2
            self.freq = {a: b >> 1 for a, b in f.items() if b > 1}

    def access(self, key):
        self._inc(key)
        if key in self.win:
            self.win.move_to_end(key); return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key] = True
            if len(self.prot) > self.pcap:
                k, _ = self.prot.popitem(last=False); self.prob[k] = True
            return True
        self.store.add(key); self.win[key] = True
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mcap:
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


class _Lfa:
    """SLRU with frequency admission and bypass: a miss is stored only if more frequent than the victim."""

    def __init__(self, capacity, prot=0.8, reset=100, cmax=63):
        self.cap = capacity
        self.pcap = int(capacity * prot)
        self.prob = OrderedDict(); self.prot = OrderedDict()
        self.freq = {}
        self.ops = 0
        self.reset = capacity * reset
        self.cmax = cmax
        self.store = _S(); self.store.ev = []

    def access(self, key):
        f = self.freq
        v = f.get(key, 0)
        if v < self.cmax:
            f[key] = v + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops //= 2
            self.freq = f = {a: b >> 1 for a, b in f.items() if b > 1}
        if key in self.prot:
            self.prot.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key] = True
            if len(self.prot) > self.pcap:
                k, _ = self.prot.popitem(last=False); self.prob[k] = True
            return True
        if len(self.store) >= self.cap:
            vq = self.prob if self.prob else self.prot
            victim = next(iter(vq))
            if f.get(key, 0) <= f.get(victim, 0):
                return False
            del vq[victim]; self.store.discard(victim)
        self.store.add(key); self.prob[key] = True
        return False



class _S3:
    """S3-FIFO."""

    def __init__(self, capacity):
        self.cap = capacity
        self.scap = max(1, capacity // 10)
        self.S = deque(); self.M = deque(); self.G = {}
        self.ghost_q = deque()
        self.freq = {}
        self.where = {}
        self.store = _S(); self.store.ev = []

    def _evict_s(self):
        while self.S:
            k = self.S.popleft()
            if self.freq[k] > 0:
                self.M.append(k); self.where[k] = 1; self.freq[k] = 0
                if len(self.M) > self.cap - self.scap:
                    self._evict_m()
                    return
            else:
                del self.freq[k]; del self.where[k]; self.store.discard(k)
                self.G[k] = True; self.ghost_q.append(k)
                while len(self.ghost_q) > self.cap:
                    g = self.ghost_q.popleft(); self.G.pop(g, None)
                return

    def _evict_m(self):
        while self.M:
            k = self.M.popleft()
            if self.freq[k] > 0:
                self.freq[k] -= 1; self.M.append(k)
            else:
                del self.freq[k]; del self.where[k]; self.store.discard(k); return

    def access(self, key):
        if key in self.where:
            if self.freq[key] < 3:
                self.freq[key] += 1
            return True
        while len(self.store) >= self.cap:
            if len(self.S) >= self.scap or not self.M:
                self._evict_s()
            else:
                self._evict_m()
        self.store.add(key); self.freq[key] = 0
        if key in self.G:
            del self.G[key]; self.M.append(key); self.where[key] = 1
        else:
            self.S.append(key); self.where[key] = 0
        return False


class _Lfu:
    """LFU over decayed history counts; a miss is stored only if more frequent than the least frequent key."""

    def __init__(self, capacity, reset=100):
        self.cap = capacity
        self.freq = {}
        self.ops = 0
        self.reset = capacity * reset
        self.heap = []
        self.t = 0
        self.store = _S(); self.store.ev = []

    def access(self, key):
        f = self.freq
        v = f.get(key, 0) + 1
        f[key] = v
        self.t += 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops //= 2
            self.freq = f = {a: b >> 1 for a, b in f.items() if b > 1 or a in self.store}
            for a in self.store:
                f[a] = max(1, f.get(a, 0))
            self.heap = [(f[a], 0, a) for a in self.store]
            heapq.heapify(self.heap)
            v = f[key] if key in f else 1
            f[key] = v
        st = self.store; h = self.heap
        if key in st:
            heapq.heappush(h, (v, self.t, key))
            return True
        if len(st) >= self.cap:
            while True:
                fv, _, k = h[0]
                if k in st and f.get(k) == fv:
                    break
                heapq.heappop(h)
            if v <= fv:
                return False
            heapq.heappop(h); st.discard(k)
        st.add(key); heapq.heappush(h, (v, self.t, key))
        return False


class Cache:
    """Follow the leader: simulate several policies, evict as the recently best one would."""

    def __init__(self, capacity, decay=16.0, margin=1.0):
        self.cap = capacity
        self.pols = [_Lirs(capacity), _Arc(capacity), _Tlfu(capacity), _Lfa(capacity), _S3(capacity), _Lfu(capacity), _Lfu(capacity, 10)]
        self.sc = [0.0] * len(self.pols)
        self.d = 1.0 - 1.0 / (capacity * decay)
        self.margin = margin
        self.lead = 0
        self.D = deque()
        self.store = set()

    def access(self, key):
        hit = key in self.store
        d = self.d; sc = self.sc
        for i, p in enumerate(self.pols):
            sc[i] = sc[i] * d + (1.0 if p.access(key) else 0.0)
        L = self.pols[self.lead]
        best = self._best()
        if best != self.lead and sc[best] > sc[self.lead] * self.margin + 1e-9:
            self.lead = best; L = self.pols[best]
            self.D = deque(k for k in self.store if k not in L.store)
        else:
            self.D.extend(L.store.ev)
        for p in self.pols:
            p.store.ev.clear()
        if not hit and key in L.store:
            st = self.store
            st.add(key)
            if len(st) > self.cap:
                D = self.D; ls = L.store
                while True:
                    k = D.popleft()
                    if k in st and k not in ls:
                        st.remove(k); break
        return hit

    def _best(self):
        sc = self.sc; b = 0
        for i in range(1, len(sc)):
            if sc[i] > sc[b]:
                b = i
        return b
