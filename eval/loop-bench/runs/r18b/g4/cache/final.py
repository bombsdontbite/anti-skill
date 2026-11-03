from collections import OrderedDict, deque
import heapq

from collections import OrderedDict, deque


class _Lirs:
    def __init__(self, capacity, hir, ghost):
        self.c = capacity
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.NR = OrderedDict()
        self.lir = set()
        self.store = {}
        self.ev = []
        self.nrmax = max(1, int(capacity * ghost))
        self.resize(hir)

    def resize(self, hir):
        self.hcap = max(1, min(self.c - 1, int(self.c * hir)))
        self.lcap = self.c - self.hcap

    def _prune(self):
        S, lir, NR = self.S, self.lir, self.NR
        while S:
            k = next(iter(S))
            if k in lir:
                return
            del S[k]
            NR.pop(k, None)

    def _demote(self):
        k, _ = self.S.popitem(last=False)
        self.lir.discard(k)
        self.Q[k] = True
        self._prune()

    def access(self, key):
        S, Q, lir = self.S, self.Q, self.lir
        if key in lir:
            S.move_to_end(key)
            self._prune()
            return True
        if key in self.store:
            if key in S:
                S.move_to_end(key)
                del Q[key]
                lir.add(key)
                self._demote()
            else:
                S[key] = True
                Q.move_to_end(key)
            return True
        store = self.store
        if len(store) >= self.c:
            if not Q:
                self._demote()
            k, _ = Q.popitem(last=False)
            del store[k]
            self.ev.append(k)
            if k in S:
                NR = self.NR
                NR[k] = True
                if len(NR) > self.nrmax:
                    g, _ = NR.popitem(last=False)
                    del S[g]
        store[key] = True
        if key in S:
            self.NR.pop(key, None)
            S.move_to_end(key)
            lir.add(key)
            self._demote()
        elif len(lir) < self.lcap:
            S[key] = True
            lir.add(key)
        else:
            S[key] = True
            Q[key] = True
        while len(lir) > self.lcap:
            self._demote()
        return False





class _Arc:

    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = {}
        self.ev = []

    def _replace(self, in_b2):
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        del self.store[k]; self.ev.append(k)

    def access(self, key):
        c = self.c
        if key in self.store:
            if key in self.t1:
                del self.t1[key]
            else:
                del self.t2[key]
            self.t2[key] = True
            return True
        if key in self.b1:
            self.p = min(c, self.p + max(len(self.b2) // len(self.b1), 1))
            self._replace(False); del self.b1[key]; self.t2[key] = True
        elif key in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // len(self.b2), 1))
            self._replace(True); del self.b2[key]; self.t2[key] = True
        else:
            l1 = len(self.t1) + len(self.b1)
            if l1 == c:
                if len(self.t1) < c:
                    self.b1.popitem(last=False); self._replace(False)
                else:
                    k, _ = self.t1.popitem(last=False); del self.store[k]; self.ev.append(k)
            elif l1 < c and l1 + len(self.t2) + len(self.b2) >= c:
                if l1 + len(self.t2) + len(self.b2) == 2 * c:
                    self.b2.popitem(last=False)
                self._replace(False)
            self.t1[key] = True
        self.store[key] = True
        return False



class _Lfu:

    def __init__(self, capacity, age=8):
        self.c = capacity
        self.store = {}
        self.ev = []
        self.cnt = {}
        self.heap = []
        self.t = 0
        self.age = capacity * age

    def access(self, key):
        cnt = self.cnt
        cnt[key] = cnt.get(key, 0) + 1
        self.t += 1
        if self.t % self.age == 0:
            self.cnt = cnt = {k: v / 2 for k, v in cnt.items() if v > 0.25}
            self.heap = [(cnt.get(k, 0), self.t, k) for k in self.store]
            heapq.heapify(self.heap)
        if key in self.store:
            heapq.heappush(self.heap, (cnt[key], self.t, key))
            return True
        st = self.store
        if len(st) >= self.c:
            h = self.heap
            while True:
                f, t, k = heapq.heappop(h)
                if k in st and cnt.get(k, 0) == f:
                    break
            if f > cnt[key]:
                heapq.heappush(h, (f, t, k))
                return False
            del st[k]
            self.ev.append(k)
        st[key] = True
        heapq.heappush(self.heap, (cnt[key], self.t, key))
        return False




class _S3:

    def __init__(self, capacity, small=0.1):
        self.c = capacity
        self.scap = max(1, int(capacity * small))
        self.S = deque(); self.M = deque()
        self.G = OrderedDict()
        self.freq = {}
        self.store = self.freq
        self.ns = 0
        self.ev = []

    def _evict(self):
        if self.ns >= self.scap or not self.M:
            while self.S:
                k = self.S.popleft(); self.ns -= 1
                if self.freq[k] > 0:
                    self.M.append(k); self.freq[k] = 0
                    if len(self.M) + self.ns <= self.c - 0:
                        if len(self.freq) <= self.c - 1 + 1 and len(self.M) + self.ns < self.c:
                            return
                else:
                    del self.freq[k]; self.ev.append(k); self.G[k] = True
                    if len(self.G) > self.c - self.scap:
                        self.G.popitem(last=False)
                    return
        while self.M:
            k = self.M.popleft()
            if self.freq[k] > 0:
                self.freq[k] -= 1; self.M.append(k)
            else:
                del self.freq[k]; self.ev.append(k); return

    def access(self, key):
        f = self.freq
        if key in f:
            if f[key] < 3:
                f[key] += 1
            return True
        while len(f) >= self.c:
            self._evict()
        f[key] = 0
        if key in self.G:
            del self.G[key]; self.M.append(key)
        else:
            self.S.append(key); self.ns += 1
        return False


class Cache:
    """Follow the leader: shadow-simulate several policies, evict what the best one dropped."""

    def __init__(self, capacity, period=0.5, decay=0.9):
        self.c = capacity
        self.store = {}
        self.shadows = [_Lirs(capacity, f, 4.0) for f in (0.01, 0.05, 0.2, 0.5)]
        self.shadows += [_Arc(capacity), _Lfu(capacity), _Lfu(capacity, 64), _S3(capacity)]
        self.scores = [0.0] * len(self.shadows)
        self.cur = 0
        self.pending = []
        self.period = max(16, int(capacity * period))
        self.decay = decay
        self.n = 0

    def _switch(self, best):
        self.cur = best
        lead = self.shadows[best].store
        self.pending = [k for k in self.store if k not in lead]

    def access(self, key):
        sc = self.scores
        for i, s in enumerate(self.shadows):
            if s.access(key):
                sc[i] += 1
        lead = self.shadows[self.cur]
        if lead.ev:
            self.pending.extend(lead.ev)
        for s in self.shadows:
            s.ev.clear()
        st = self.store
        hit = key in st
        if not hit:
            st[key] = True
            if key not in lead.store:
                self.pending.append(key)
            if len(st) > self.c:
                p = self.pending
                ls = lead.store
                while True:
                    if not p:
                        p.extend(k for k in st if k not in ls)
                    k = p.pop()
                    if k in st and k not in ls:
                        break
                del st[k]
        self.n += 1
        if self.n >= self.period:
            self.n = 0
            best = self.cur
            for i in range(len(sc)):
                if sc[i] > sc[best]:
                    best = i
            if best != self.cur:
                self._switch(best)
            d = self.decay
            self.scores = [x * d for x in sc]
        return hit
