from collections import OrderedDict, deque
import heapq
import math




class Lirs:
    def __init__(self, capacity, hfrac, ghost=4):
        self.capacity = capacity
        self.hcap = max(1, int(capacity * hfrac))
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.G = OrderedDict()
        self.gmax = ghost * capacity
        self.lir = set()
        self.store = set()
        self.ev = []

    def _prune(self):
        S, lir = self.S, self.lir
        while S:
            k = next(iter(S))
            if k in lir:
                break
            del S[k]

    def _demote(self):
        S = self.S
        b = next(iter(S))
        self.lir.discard(b); del S[b]; self.Q[b] = True
        self._prune()

    def access(self, x):
        S, Q, lir, store = self.S, self.Q, self.lir, self.store
        if x in lir:
            first = next(iter(S)) == x
            S.move_to_end(x)
            if first:
                self._prune()
            return True
        hit = x in store
        lcap = self.capacity - self.hcap
        if not hit:
            self.G.pop(x, None)
            if len(store) >= self.capacity:
                if Q:
                    k, _ = Q.popitem(last=False)
                else:
                    k = next(iter(S))
                    lir.discard(k); del S[k]; self._prune()
                store.discard(k)
                self.ev.append(k)
                self.G[k] = True
                if len(self.G) > self.gmax:
                    g, _ = self.G.popitem(last=False)
                    S.pop(g, None)
            store.add(x)
            if len(lir) < lcap and len(store) <= lcap:
                S[x] = True; lir.add(x)
                return False
        if x in S:
            S.move_to_end(x)
            Q.pop(x, None)
            lir.add(x)
        else:
            S[x] = True
            Q[x] = True; Q.move_to_end(x)
        while len(lir) > lcap:
            self._demote()
        return hit



class Wtlfu:
    """W-TinyLFU: LRU window, SLRU main, frequency admission with aging."""

    def __init__(self, capacity, wfrac=0.01, reset=10):
        self.capacity = capacity
        self.store = {}
        self.ev = []
        self.wcap = max(1, int(capacity * wfrac))
        mcap = capacity - self.wcap
        self.pcap = max(1, int(mcap * 0.8))
        self.window = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.freq = {}
        self.ops = 0
        self.reset = reset * capacity

    def _inc(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = {k: v >> 1 for k, v in f.items() if v > 1}

    def access(self, key):
        self._inc(key)
        if key in self.store:
            if key in self.window:
                self.window.move_to_end(key)
            elif key in self.prot:
                self.prot.move_to_end(key)
            else:
                del self.prob[key]
                self.prot[key] = True
                if len(self.prot) > self.pcap:
                    k, _ = self.prot.popitem(last=False)
                    self.prob[k] = True
            return True
        self.store[key] = True
        self.window[key] = True
        if len(self.window) > self.wcap:
            cand, _ = self.window.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.capacity - self.wcap:
                self.prob[cand] = True
            else:
                victim = next(iter(self.prob)) if self.prob else next(iter(self.prot))
                f = self.freq
                if f.get(cand, 0) > f.get(victim, 0):
                    if victim in self.prob:
                        del self.prob[victim]
                    else:
                        del self.prot[victim]
                    del self.store[victim]
                    self.ev.append(victim)
                    self.prob[cand] = True
                else:
                    del self.store[cand]
                    self.ev.append(cand)
        return False


class S3fifo:
    """S3-FIFO."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.scap = max(1, capacity // 10)
        self.small = deque(); self.main = deque()
        self.ghost = OrderedDict()
        self.freq = {}
        self.store = self.freq
        self.nsmall = 0
        self.ev = []

    def _evict(self):
        f = self.freq
        if self.nsmall >= self.scap or not self.main:
            while self.small:
                k = self.small.popleft(); self.nsmall -= 1
                if f[k] > 0:
                    f[k] = 0; self.main.append(k)
                else:
                    del f[k]; self.ev.append(k); self.ghost[k] = True
                    if len(self.ghost) > self.capacity - self.scap:
                        self.ghost.popitem(last=False)
                    return
        while True:
            k = self.main.popleft()
            if f[k] > 0:
                f[k] -= 1; self.main.append(k)
            else:
                del f[k]; self.ev.append(k); return

    def access(self, key):
        f = self.freq
        if key in f:
            if f[key] < 3:
                f[key] += 1
            return True
        if len(f) >= self.capacity:
            self._evict()
        f[key] = 0
        if key in self.ghost:
            del self.ghost[key]; self.main.append(key)
        else:
            self.small.append(key); self.nsmall += 1
        return False


class Lrfu:
    """LRFU: evict the lowest exponentially decayed access count, kept in log2 form."""

    def __init__(self, capacity, half=10, admit=False, hist=8):
        self.capacity = capacity
        self.lam = 1.0 / (half * capacity)
        self.store = {}
        self.val = {}
        self.heap = []
        self.t = 0
        self.admit = admit
        self.hist = hist * capacity
        self.ev = []

    def access(self, key):
        self.t += 1
        lt = self.lam * self.t
        val, st = self.val, self.store
        old = val.get(key)
        if old is None or old - lt < -60:
            v = lt
        else:
            v = lt + math.log2(1.0 + 2.0 ** (old - lt))
        val[key] = v
        hit = key in st
        if not hit and len(st) >= self.capacity:
            h = self.heap
            while st.get(h[0][1]) != h[0][0]:
                heapq.heappop(h)
            if self.admit and v < h[0][0]:
                return False
            k = heapq.heappop(h)[1]
            del st[k]
            self.ev.append(k)
        st[key] = v
        heapq.heappush(self.heap, (v, key))
        if len(val) > self.hist + self.capacity:
            cut = lt - 30
            for k in [k for k, x in val.items() if x < cut and k not in st]:
                del val[k]
            if len(val) > self.hist:
                self.hist = 2 * len(val)
        if len(self.heap) > 4 * self.capacity:
            self.heap = [(x, k) for k, x in st.items()]
            heapq.heapify(self.heap)
        return hit


class Cache:
    """Runs several policies on keys only and keeps the real cache converging to the recent leader."""

    def __init__(self, capacity, win=20, which="lwsf"):
        self.capacity = capacity
        make = {"l": lambda: Lirs(capacity, 0.01), "w": lambda: Wtlfu(capacity, 0.01, 100),
                "s": lambda: S3fifo(capacity), "f": lambda: Lrfu(capacity, 1)}
        self.pol = [make[c]() for c in which]
        self.sc = [0.0] * len(self.pol)
        self.d = 1.0 - 1.0 / (win * capacity)
        self.lead = 0
        self.store = set()
        self.pend = deque()

    def access(self, x):
        d = self.d
        sc = self.sc
        best = self.lead
        for i, p in enumerate(self.pol):
            sc[i] = sc[i] * d + p.access(x)
            if p.ev:
                if i == best:
                    self.pend.extend(p.ev)
                p.ev.clear()
        for i in range(len(sc)):
            if sc[i] > sc[best] + 1e-9:
                best = i
        if best != self.lead:
            self.lead = best
            self.pend.clear()
        store = self.store
        if x in store:
            return True
        if len(store) >= self.capacity:
            ls = self.pol[self.lead].store
            pend = self.pend
            v = None
            while pend:
                k = pend.popleft()
                if k in store and k not in ls and k != x:
                    v = k
                    break
            if v is None:
                for k in store:
                    if k not in ls:
                        v = k
                        break
            store.discard(v)
        store.add(x)
        return False
