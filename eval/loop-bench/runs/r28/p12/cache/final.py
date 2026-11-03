import heapq
from collections import OrderedDict, deque




class LIRS:
    """LIRS, with non-resident HIR entries bounded by a FIFO."""

    def __init__(self, capacity, hir=0.05, ghost=5.0):
        self.capacity = capacity
        self.ev = deque(maxlen=capacity)
        self.store = {}
        self.hcap = max(1, int(capacity * hir))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.G = OrderedDict()
        self.lir = set()
        self.gcap = int(capacity * ghost)

    def _prune(self):
        S, lir, G = self.S, self.lir, self.G
        while S:
            k = next(iter(S))
            if k in lir:
                return
            del S[k]
            G.pop(k, None)

    def access(self, key):
        S, Q, lir, G = self.S, self.Q, self.lir, self.G
        if key in lir:
            first = next(iter(S)) == key
            S.move_to_end(key)
            if first:
                self._prune()
            return True
        hit = key in self.store
        if hit:
            del Q[key]
        else:
            if len(self.store) >= self.capacity:
                k, _ = Q.popitem(last=False)
                del self.store[k]
                self.ev.append(k)
                if k in S:
                    G[k] = True
                    if len(G) > self.gcap:
                        g, _ = G.popitem(last=False)
                        del S[g]
            self.store[key] = True
        if key in S or len(lir) < self.lcap:
            G.pop(key, None)
            S[key] = True
            S.move_to_end(key)
            lir.add(key)
            if len(lir) > self.lcap:
                b = next(iter(S))
                lir.discard(b)
                del S[b]
                Q[b] = True
                self._prune()
        else:
            S[key] = True
            Q[key] = True
        return hit


class WTLFU:
    """W-TinyLFU: small LRU window, frequency-gated admission into an SLRU main area."""

    def __init__(self, capacity, window=0.01, protected=0.8, sample=10):
        self.capacity = capacity
        self.ev = deque(maxlen=capacity)
        self.store = {}
        self.wcap = max(1, int(capacity * window))
        self.mcap = capacity - self.wcap
        self.pcap = int(self.mcap * protected)
        self.win = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.freq = {}
        self.ops = 0
        self.reset = sample * capacity

    def _inc(self, key):
        f = self.freq
        v = f.get(key, 0)
        if v < 15:
            f[key] = v + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = {k: v >> 1 for k, v in f.items() if v > 1}

    def access(self, key):
        self._inc(key)
        if key in self.store:
            if key in self.win:
                self.win.move_to_end(key)
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
        self.win[key] = True
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mcap:
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




class ARC:
    """ARC."""

    def __init__(self, capacity):
        self.c = capacity
        self.ev = deque(maxlen=capacity)
        self.store = {}
        self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()

    def _replace(self, inb2):
        if self.t1 and (len(self.t1) > self.p or (inb2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        del self.store[k]
        self.ev.append(k)

    def access(self, key):
        c = self.c
        if key in self.t1:
            del self.t1[key]; self.t2[key] = True; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p = min(c, self.p + max(1, len(self.b2) // len(self.b1)))
            self._replace(False); del self.b1[key]; self.t2[key] = True
        elif key in self.b2:
            self.p = max(0, self.p - max(1, len(self.b1) // len(self.b2)))
            self._replace(True); del self.b2[key]; self.t2[key] = True
        else:
            l1 = len(self.t1) + len(self.b1)
            if l1 == c:
                if len(self.t1) < c:
                    self.b1.popitem(last=False); self._replace(False)
                else:
                    k, _ = self.t1.popitem(last=False); del self.store[k]; self.ev.append(k)
            elif l1 < c:
                tot = l1 + len(self.t2) + len(self.b2)
                if tot >= c:
                    if tot == 2 * c:
                        self.b2.popitem(last=False)
                    self._replace(False)
            self.t1[key] = True
        self.store[key] = True
        return False


class LFU:
    """LFU with aged counts; a new key replaces the least-frequent one only if it is more frequent."""

    def __init__(self, capacity, sample=10, strict=True):
        self.capacity = capacity
        self.ev = deque(maxlen=capacity)
        self.store = {}
        self.freq = {}
        self.heap = []
        self.ops = 0
        self.reset = sample * capacity
        self.t = 0
        self.strict = strict

    def access(self, key):
        f = self.freq
        v = f.get(key, 0) + 1
        f[key] = v
        self.t += 1
        self.ops += 1
        st = self.store
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = f = {k: c >> 1 for k, c in f.items() if c > 1 or k in st}
            for k in st:
                st[k] = f.get(k, 0)
            self.heap = [(c, 0, k) for k, c in st.items()]
            heapq.heapify(self.heap)
            v = f.get(key, 0)
        h = self.heap
        if key in st:
            st[key] = v
            heapq.heappush(h, (v, self.t, key))
            return True
        if len(st) >= self.capacity:
            while True:
                c, _, k = h[0]
                if st.get(k) == c:
                    break
                heapq.heappop(h)
            if self.strict and v <= c:
                return False
            heapq.heappop(h)
            del st[k]
            self.ev.append(k)
        st[key] = v
        heapq.heappush(h, (v, self.t, key))
        if len(h) > 4 * self.capacity:
            self.heap = h = [(c, 0, k) for k, c in st.items()]
            heapq.heapify(h)
        return False


class LRU:
    def __init__(self, capacity):
        self.capacity = capacity
        self.ev = deque(maxlen=capacity)
        self.store = OrderedDict()

    def access(self, key):
        if key in self.store:
            self.store.move_to_end(key)
            return True
        if len(self.store) >= self.capacity:
            self.ev.append(self.store.popitem(last=False)[0])
        self.store[key] = True
        return False


class MRU:
    def __init__(self, capacity):
        self.capacity = capacity
        self.ev = deque(maxlen=capacity)
        self.store = {}
        self.last = None

    def access(self, key):
        st = self.store
        if key in st:
            self.last = key
            return True
        if len(st) >= self.capacity:
            del st[self.last]
            self.ev.append(self.last)
        st[key] = True
        self.last = key
        return False


class Cache:
    """Simulates several policies and evicts toward the one with the most recent hits."""

    def __init__(self, capacity, half=10.0, margin=1.0, experts=None):
        if experts is None:
            experts = (LIRS, LRU, lambda c: WTLFU(c, sample=100), lambda c: LIRS(c, hir=0.01, ghost=10.0))
        self.margin = margin
        self.capacity = capacity
        self.ev = deque(maxlen=capacity)
        self.store = OrderedDict()
        self.experts = [E(capacity) for E in experts]
        self.score = [0.0] * len(self.experts)
        self.decay = 0.5 ** (1.0 / (half * capacity))
        self.leader = 0

    def access(self, key):
        sc = self.score
        d = self.decay
        best = 0
        for i, e in enumerate(self.experts):
            sc[i] = sc[i] * d + (1.0 if e.access(key) else 0.0)
            if sc[i] > sc[best]:
                best = i
        if sc[best] > sc[self.leader] * self.margin:
            self.leader = best
        st = self.store
        if key in st:
            st.move_to_end(key)
            return True
        if len(st) >= self.capacity:
            e = self.experts[self.leader]
            ls, ev = e.store, e.ev
            while ev:
                k = ev.pop()
                if k in st and k not in ls:
                    break
            else:
                for k in st:
                    if k not in ls:
                        break
            del st[k]
        st[key] = True
        return False
