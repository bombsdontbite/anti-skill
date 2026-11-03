import heapq
from collections import OrderedDict


class TLFU:
    """W-TinyLFU: 1% LRU window, SLRU main, frequency-sketch admission with aging."""

    def __init__(self, capacity, wfrac=0.01, pfrac=0.8, reset=10):
        self.cap = capacity
        self.wcap = max(1, int(capacity * wfrac))
        self.mcap = capacity - self.wcap
        self.pcap = int(self.mcap * pfrac)
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.freq = {}
        self.ops = 0
        self.reset = reset * capacity
        self.store = set()

    def _inc(self, k):
        f = self.freq
        f[k] = f.get(k, 0) + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
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
        self.win[key] = True; self.store.add(key)
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = True
            else:
                vict = next(iter(self.prob)) if self.prob else next(iter(self.prot))
                f = self.freq
                if f.get(cand, 0) > f.get(vict, 0):
                    if vict in self.prob: del self.prob[vict]
                    else: del self.prot[vict]
                    self.store.discard(vict); self.prob[cand] = True
                else:
                    self.store.discard(cand)
        return False


class LIRS:
    """LIRS with 1% HIR resident set."""

    def __init__(self, capacity, hfrac=0.01):
        self.cap = capacity
        self.hcap = max(1, int(capacity * hfrac))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict()  # key -> True if LIR
        self.Q = OrderedDict()  # resident HIR
        self.nlir = 0
        self.store = set()

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if S[k]: break
            del S[k]
        if len(S) > 3 * self.cap:
            for k in list(S)[: len(S) - 2 * self.cap]:
                if not S[k]: del S[k]

    def access(self, key):
        S, Q = self.S, self.Q
        if key in self.store:
            if key in S and S[key]:
                S.move_to_end(key); self._prune(); return True
            if key in S:
                del S[key]; S[key] = True; del Q[key]; self.nlir += 1
                k = next(iter(S)); del S[k]; self.nlir -= 1; Q[k] = True
                self._prune()
            else:
                S[key] = False; Q.move_to_end(key)
            return True
        if self.nlir < self.lcap:
            S[key] = True; self.nlir += 1; self.store.add(key); return False
        if len(Q) >= self.hcap:
            k, _ = Q.popitem(last=False); self.store.discard(k)
        self.store.add(key)
        if key in S:
            del S[key]; S[key] = True; self.nlir += 1
            k = next(iter(S)); del S[k]; self.nlir -= 1; Q[k] = True
            self._prune()
        else:
            S[key] = False; Q[key] = True
        return False


class PB:
    """Predicted Belady: next use = last use + last reuse interval; evict the furthest."""

    def __init__(self, capacity, dflt=4.0, hist=8, alpha=1.0):
        self.cap = capacity
        self.dflt = dflt * capacity
        self.alpha = alpha
        self.last = {}; self.ivl = {}
        self.hist = hist * capacity
        self.heap = []; self.pred = {}
        self.t = 0
        self.store = set()

    def _rebuild(self):
        t = self.t
        h = []
        for k in self.store:
            p = self.last[k] + self.ivl.get(k, self.dflt)
            if p < t:
                p = t + (t - self.last[k])
            self.pred[k] = p
            h.append((-p, k))
        heapq.heapify(h)
        self.heap = h
        if len(self.last) > self.hist:
            keep = sorted(self.last, key=self.last.get)[-self.hist // 2:]
            ks = set(keep) | self.store
            self.last = {k: self.last[k] for k in ks}
            self.ivl = {k: v for k, v in self.ivl.items() if k in ks}

    def access(self, key):
        self.t = t = self.t + 1
        if t % self.cap == 0:
            self._rebuild()
        lt = self.last.get(key)
        if lt is not None:
            d = t - lt
            o = self.ivl.get(key)
            self.ivl[key] = d if o is None else o + self.alpha * (d - o)
        self.last[key] = t
        p = t + self.ivl.get(key, self.dflt)
        st = self.store
        if key in st:
            self.pred[key] = p
            heapq.heappush(self.heap, (-p, key))
            return True
        if len(st) >= self.cap:
            h = self.heap
            while True:
                np_, k = h[0]
                if k in st and self.pred[k] == -np_:
                    break
                heapq.heappop(h)
            if p >= -np_:
                return False
            heapq.heappop(h); st.discard(k); del self.pred[k]
        st.add(key); self.pred[key] = p
        heapq.heappush(self.heap, (-p, key))
        return False


class Cache:
    """Simulate several policies; follow the one with the most recent hits, evicting toward its set."""

    def __init__(self, capacity, half=10.0, margin=0.02):
        self.cap = capacity
        self.ex = [TLFU(capacity, 0.01, 0.8, 30), LIRS(capacity),
                   PB(capacity, 1.0, 8, 0.25), PB(capacity, 16.0, 8, 0.25)]
        self.w = [0.0] * len(self.ex)
        self.decay = 0.5 ** (1.0 / (half * capacity))
        self.store = OrderedDict()
        self.lead = 0
        self.margin = margin

    def access(self, key):
        d = self.decay; w = self.w
        for i, e in enumerate(self.ex):
            w[i] = w[i] * d + (1.0 if e.access(key) else 0.0)
        st = self.store
        if key in st:
            st.move_to_end(key); return True
        b = max(range(len(w)), key=lambda i: w[i])
        if w[b] > w[self.lead] * (1.0 + self.margin) + 1e-9:
            self.lead = b
        best = self.ex[self.lead].store
        if key not in best:
            return False
        if len(st) >= self.cap:
            while True:
                k = next(iter(st))
                if k not in best:
                    break
                st.move_to_end(k)
            del st[k]
        st[key] = True
        return False
