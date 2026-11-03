import heapq
from collections import OrderedDict


class LRU:
    def __init__(self, capacity):
        self.cap = capacity
        self.store = OrderedDict()
        self.ev = []

    def access(self, key):
        st = self.store
        if key in st:
            st.move_to_end(key)
            return True
        if len(st) >= self.cap:
            self.ev.append(st.popitem(last=False)[0])
        st[key] = None
        return False


class LIRS:
    def __init__(self, capacity, hir=0.01, ghost=8.0):
        self.cap = capacity
        self.lcap = capacity - max(1, int(capacity * hir))
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.G = OrderedDict()
        self.lir = set()
        self.store = {}
        self.gmax = max(1, int(ghost * capacity))
        self.ev = []

    def _prune(self):
        S, lir, G = self.S, self.lir, self.G
        while S:
            k = next(iter(S))
            if k in lir:
                break
            del S[k]
            if k in G:
                del G[k]

    def _promote(self, key):
        S = self.S
        S.move_to_end(key)
        self.lir.add(key)
        k = next(iter(S))
        self.lir.discard(k)
        del S[k]
        self.Q[k] = None
        self._prune()

    def access(self, key):
        S, Q, lir, st = self.S, self.Q, self.lir, self.store
        if key in lir:
            S.move_to_end(key)
            self._prune()
            return True
        if key in st:
            if key in S:
                del Q[key]
                self._promote(key)
            else:
                S[key] = None
                Q.move_to_end(key)
            return True
        if len(lir) < self.lcap:
            lir.add(key)
            S[key] = None
            st[key] = None
            if key in self.G:
                del self.G[key]
            return False
        if len(st) >= self.cap:
            k = Q.popitem(last=False)[0]
            del st[k]
            self.ev.append(k)
            if k in S:
                self.G[k] = None
                if len(self.G) > self.gmax:
                    del S[self.G.popitem(last=False)[0]]
        st[key] = None
        if key in S:
            del self.G[key]
            self._promote(key)
        else:
            S[key] = None
            Q[key] = None
        return False


class TinyLFU:
    def __init__(self, capacity, win=0.01):
        self.cap = capacity
        self.wcap = max(1, int(capacity * win))
        self.mcap = capacity - self.wcap
        self.pcap = int(self.mcap * 0.8)
        self.win = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.freq = {}
        self.ops = 0
        self.reset = 10 * capacity
        self.store = {}
        self.ev = []

    def access(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = f = {a: b >> 1 for a, b in f.items() if b > 1}
        if key in self.win:
            self.win.move_to_end(key)
            return True
        if key in self.prot:
            self.prot.move_to_end(key)
            return True
        if key in self.prob:
            del self.prob[key]
            self.prot[key] = None
            if len(self.prot) > self.pcap:
                self.prob[self.prot.popitem(last=False)[0]] = None
            return True
        self.win[key] = None
        self.store[key] = None
        if len(self.win) > self.wcap:
            cand = self.win.popitem(last=False)[0]
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = None
            else:
                vq = self.prob if self.prob else self.prot
                victim = next(iter(vq))
                if f.get(cand, 0) > f.get(victim, 0):
                    del vq[victim]
                    del self.store[victim]
                    self.ev.append(victim)
                    self.prob[cand] = None
                else:
                    del self.store[cand]
                    self.ev.append(cand)
        return False


class LFU:
    """Frequency with slow halving; evicts min (freq, last use) among residents via lazy heap."""
    def __init__(self, capacity, reset=50):
        self.cap = capacity
        self.store = {}
        self.freq = {}
        self.heap = []
        self.t = 0
        self.ops = 0
        self.reset = reset * capacity
        self.ev = []

    def access(self, key):
        self.t += 1
        f = self.freq
        c = f.get(key, 0) + 1
        f[key] = c
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = f = {a: b >> 1 for a, b in f.items() if b > 1 or a in self.store}
            self.heap = [(f.get(k, 0), t, k) for k, t in self.store.items()]
            heapq.heapify(self.heap)
        st = self.store
        if key in st:
            st[key] = self.t
            heapq.heappush(self.heap, (c, self.t, key))
            return True
        h = self.heap
        if len(st) >= self.cap:
            while True:
                fc, t, k = heapq.heappop(h)
                if st.get(k) == t and f.get(k, 0) == fc:
                    break
            if fc > c:
                heapq.heappush(h, (fc, t, k))
                return False
            del st[k]
            self.ev.append(k)
        st[key] = self.t
        heapq.heappush(h, (c, self.t, key))
        if len(h) > 4 * self.cap + 100:
            self.heap = [(f.get(k, 0), t, k) for k, t in st.items()]
            heapq.heapify(self.heap)
        return False


class Cache:
    """Runs LIRS, LRU, W-TinyLFU and LFU as shadow caches and follows whichever has the most recent (decayed) hits."""

    def __init__(self, capacity, halflife=8.0, amargin=0.05):
        self.cap = capacity
        self.experts = [LIRS(capacity), LRU(capacity), TinyLFU(capacity), LFU(capacity)]
        self.score = [0.0] * len(self.experts)
        self.decay = 0.5 ** (1.0 / (halflife * capacity))
        self.inc = 1.0
        self.lead = 0
        self.store = OrderedDict()
        self.diff = set()
        self.amargin = amargin * capacity

    def access(self, key):
        experts = self.experts
        sc = self.score
        self.inc /= self.decay
        if self.inc > 1e100:
            sc[:] = [s / self.inc for s in sc]
            self.inc = 1.0
        for i, e in enumerate(experts):
            if e.access(key):
                sc[i] += self.inc
        lead = self.lead
        best = 0
        for i in range(1, len(sc)):
            if sc[i] > sc[best]:
                best = i
        if sc[best] > sc[lead] * 1.02 + self.amargin * self.inc:
            lead = self.lead = best
            ls = experts[lead].store
            self.diff = {k for k in self.store if k not in ls}
        else:
            ls = experts[lead].store
            st = self.store
            for k in experts[lead].ev:
                if k in st:
                    self.diff.add(k)
        for e in experts:
            e.ev.clear()
        st = self.store
        if key in st:
            st.move_to_end(key)
            if key in ls:
                self.diff.discard(key)
            return True
        if key in ls:
            if len(st) >= self.cap:
                diff = self.diff
                if diff:
                    del st[diff.pop()]
                else:
                    st.popitem(last=False)
            st[key] = None
        return False
